from io import BytesIO

from swifthire.assessments.service import get_assessment_service
from swifthire import create_app
from swifthire.applications.service import get_application_service
from swifthire.coding.runner import ExecutionResult
from swifthire.coding.service import CodingChallengeService
from swifthire.jobs.service import get_job_service
from swifthire.workflow.service import get_workflow_service


class FakeRunner:
    def __init__(self, results):
        self.results = list(results)

    def run(self, source, language, stdin, timeout_seconds):
        return self.results.pop(0)


def _register_recruiter(client, email: str):
    response = client.post('/api/auth/register', json={
        'name': 'Recruiter',
        'email': email,
        'password': 'secret123',
    })
    assert response.status_code == 201
    return response.get_json()['user']


def _create_job(client, title='Senior Designer', slug='senior-designer'):
    response = client.post('/api/recruiter/jobs', json={
        'title': title,
        'description': 'Design product experiences.',
        'status': 'published',
        'public_slug': slug,
    })
    assert response.status_code == 201
    return response.get_json()


def _apply(client, slug: str, email: str):
    response = client.post(
        f'/api/public/jobs/{slug}/applications',
        data={
            'name': 'Jane Candidate',
            'email': email,
            'cv': (BytesIO(b'%PDF-1.4\nBT\n(Resume) Tj\nET\n%%EOF'), 'resume.pdf', 'application/pdf'),
        },
        content_type='multipart/form-data',
    )
    assert response.status_code == 201
    return response.get_json()


def test_dashboard_requires_recruiter_auth():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    client = app.test_client()
    recruiter = _register_recruiter(client, 'owner@example.com')
    job = _create_job(client)

    response = client.get(f"/api/recruiter/jobs/{job['id']}/dashboard")
    assert response.status_code == 200

    other_client = app.test_client()
    response = other_client.get(f"/api/recruiter/jobs/{job['id']}/dashboard")
    assert response.status_code == 401


def test_dashboard_is_scoped_to_job_owner():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    owner_client = app.test_client()
    other_client = app.test_client()

    _register_recruiter(owner_client, 'owner-a@example.com')
    _register_recruiter(other_client, 'owner-b@example.com')

    owner_job = _create_job(owner_client, title='Product Designer', slug='product-designer')
    other_job = _create_job(other_client, title='Data Analyst', slug='data-analyst')

    owner_client.post(f"/api/public/jobs/{owner_job['public_slug']}/applications", data={
        'name': 'Candidate One',
        'email': 'candidate-one@example.com',
        'cv': (BytesIO(b'%PDF-1.4\nBT\n(Resume) Tj\nET\n%%EOF'), 'resume.pdf', 'application/pdf'),
    }, content_type='multipart/form-data')
    other_client.post(f"/api/public/jobs/{other_job['public_slug']}/applications", data={
        'name': 'Candidate Two',
        'email': 'candidate-two@example.com',
        'cv': (BytesIO(b'%PDF-1.4\nBT\n(Resume) Tj\nET\n%%EOF'), 'resume.pdf', 'application/pdf'),
    }, content_type='multipart/form-data')

    dashboard = owner_client.get(f"/api/recruiter/jobs/{owner_job['id']}/dashboard")
    assert dashboard.status_code == 200
    payload = dashboard.get_json()
    assert payload['job']['id'] == owner_job['id']
    assert payload['counts']['total'] == 1
    assert len(payload['candidates']) == 1
    assert payload['candidates'][0]['status'] in {'pending', 'recommended', 'rejected', 'advanced'}


def test_dashboard_counts_only_returned_candidates():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    client = app.test_client()
    _register_recruiter(client, 'count-owner@example.com')
    job = _create_job(client, title='UX Researcher', slug='ux-researcher')

    for index in range(3):
        _apply(client, job['public_slug'], f'candidate-{index}@example.com')

    response = client.get(f"/api/recruiter/jobs/{job['id']}/dashboard")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload['counts']['total'] == len(payload['candidates']) == 3
    assert sum(payload['counts']['by_status'].values()) == payload['counts']['total']


def test_stage_result_states_do_not_invent_scores():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    client = app.test_client()
    _register_recruiter(client, 'stage-owner@example.com')
    job = _create_job(client, title='Marketing Lead', slug='marketing-lead')
    application = _apply(client, job['public_slug'], 'marketer@example.com')

    response = client.get(f"/api/recruiter/jobs/{job['id']}/dashboard")
    assert response.status_code == 200
    payload = response.get_json()
    candidate = payload['candidates'][0]
    assert candidate['match_result']['score'] is None
    assert candidate['stage_results'][0]['score'] is None
    assert candidate['match_result']['state'] in {'pending', 'failed', 'unavailable'}


def test_dashboard_omits_private_artifacts():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    client = app.test_client()
    _register_recruiter(client, 'private-owner@example.com')
    job = _create_job(client, title='Engineer', slug='engineer')
    _apply(client, job['public_slug'], 'engineer-candidate@example.com')

    response = client.get(f"/api/recruiter/jobs/{job['id']}/dashboard")
    assert response.status_code == 200
    payload = response.get_json()
    serialized = str(payload)
    assert 'resume.pdf' not in serialized
    assert 'object_key' not in serialized
    assert 'provider' not in serialized.lower()
    assert 'transcript' not in serialized.lower()
    assert 'audio' not in serialized.lower()


def test_decision_action_delegates_to_phase3_service():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    client = app.test_client()
    _register_recruiter(client, 'decision-owner@example.com')
    job = _create_job(client, title='Operations Manager', slug='operations-manager')
    application = _apply(client, job['public_slug'], 'ops@example.com')

    response = client.post(
        f"/api/recruiter/applications/{application['id']}/decisions",
        json={'decision': 'advance', 'expected_stage': 'online_assessment'},
    )
    assert response.status_code == 201
    payload = response.get_json()
    assert payload['decision'] == 'advance'
    assert payload['expected_stage'] == 'online_assessment'


def test_missing_and_failed_results_have_no_score():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    client = app.test_client()
    recruiter = _register_recruiter(client, 'missing-result-owner@example.com')
    job = _create_job(client, title='Engineer', slug='missing-result-engineer')
    application = _apply(client, job['public_slug'], 'missing@example.com')

    with app.app_context():
        service = CodingChallengeService(runner=FakeRunner([
            ExecutionResult('timeout', '', 'Timed out.', 10),
        ]))
        app.extensions['coding_service'] = service
        challenge = service.create_challenge(
            job['id'],
            recruiter['id'],
            'Private challenge',
            'Solve the problem.',
            ['python'],
            private_test_cases=[{'input': '', 'expected_output': 'secret'}],
        )
        service.create_submission(challenge.id, application['id'], 'python', 'private source')

    response = client.get(f"/api/recruiter/jobs/{job['id']}/dashboard")
    assert response.status_code == 200
    candidate = response.get_json()['candidates'][0]
    stages = {result['stage_key']: result for result in candidate['stage_results']}
    assert stages['online_assessment']['state'] == 'pending'
    assert stages['online_assessment']['score'] is None
    assert stages['coding_assessment']['state'] == 'unavailable'
    assert stages['coding_assessment']['score'] is None
    assert stages['voice_interview']['state'] == 'not_configured'
    assert stages['voice_interview']['score'] is None


def test_completed_assessment_and_coding_results_are_aggregated():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    client = app.test_client()
    recruiter = _register_recruiter(client, 'completed-result-owner@example.com')
    job = _create_job(client, title='Engineer', slug='completed-result-engineer')
    first_application = _apply(client, job['public_slug'], 'first@example.com')
    second_application = _apply(client, job['public_slug'], 'second@example.com')

    with app.app_context():
        assessment = get_assessment_service().create_assessment(
            first_application['id'],
            job['id'],
            'online_assessment',
        )
        assessment.status = 'submitted'
        assessment.score = 82

        service = CodingChallengeService(runner=FakeRunner([
            ExecutionResult('completed', 'one', '', 1, 0),
            ExecutionResult('completed', 'two', '', 1, 0),
            ExecutionResult('completed', 'one', '', 1, 0),
            ExecutionResult('completed', 'wrong', '', 1, 0),
        ]))
        app.extensions['coding_service'] = service
        challenge = service.create_challenge(
            job['id'],
            recruiter['id'],
            'Private challenge',
            'Solve the problem.',
            ['python'],
            private_test_cases=[
                {'input': 'first', 'expected_output': 'one'},
                {'input': 'second', 'expected_output': 'two'},
            ],
        )
        service.create_submission(challenge.id, first_application['id'], 'python', 'private source')
        service.create_submission(challenge.id, second_application['id'], 'python', 'another private source')

    response = client.get(f"/api/recruiter/jobs/{job['id']}/dashboard")
    assert response.status_code == 200
    payload = response.get_json()
    candidates = {candidate['application_id']: candidate for candidate in payload['candidates']}
    first_stages = {result['stage_key']: result for result in candidates[first_application['id']]['stage_results']}
    second_stages = {result['stage_key']: result for result in candidates[second_application['id']]['stage_results']}
    assert first_stages['online_assessment']['state'] == 'completed'
    assert first_stages['online_assessment']['score'] == 82
    assert first_stages['coding_assessment']['state'] == 'completed'
    assert first_stages['coding_assessment']['score'] == 100
    assert second_stages['coding_assessment']['state'] == 'completed'
    assert second_stages['coding_assessment']['score'] == 50
    serialized = str(payload)
    assert 'private source' not in serialized
    assert 'another private source' not in serialized
    assert 'secret' not in serialized


def test_decisions_are_listed_without_private_workflow_access():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    client = app.test_client()
    recruiter = _register_recruiter(client, 'decision-history-owner@example.com')
    job = _create_job(client, title='Engineer', slug='decision-history-engineer')
    application = _apply(client, job['public_slug'], 'decision-history@example.com')

    with app.app_context():
        get_workflow_service().decide(
            job_id=job['id'],
            application_id=application['id'],
            recruiter_id=recruiter['id'],
            decision='advance',
            expected_stage='online_assessment',
        )

    response = client.get(f"/api/recruiter/jobs/{job['id']}/dashboard")
    assert response.status_code == 200
    candidate = response.get_json()['candidates'][0]
    assert candidate['decision_history'][0]['decision'] == 'advance'
    assert candidate['decision_history'][0]['expected_stage'] == 'online_assessment'


def test_available_actions_follow_application_stage_and_status():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    client = app.test_client()
    _register_recruiter(client, 'actions-owner@example.com')
    job = _create_job(client, title='Engineer', slug='actions-engineer')
    application = _apply(client, job['public_slug'], 'actions@example.com')

    with app.app_context():
        record = get_application_service().get_by_id(application['id'])
        record.current_stage = 'not-configured'

    response = client.get(f"/api/recruiter/jobs/{job['id']}/dashboard")
    assert response.status_code == 200
    assert response.get_json()['candidates'][0]['available_actions'] == []

    with app.app_context():
        record.current_stage = 'online_assessment'
        record.status = 'rejected'

    response = client.get(f"/api/recruiter/jobs/{job['id']}/dashboard")
    assert response.status_code == 200
    assert response.get_json()['candidates'][0]['available_actions'] == []

    with app.app_context():
        record.status = 'pending'

    response = client.get(f"/api/recruiter/jobs/{job['id']}/dashboard")
    assert response.status_code == 200
    actions = response.get_json()['candidates'][0]['available_actions']
    assert actions == [
        {'decision': 'advance', 'expected_stage': 'online_assessment'},
        {'decision': 'reject', 'expected_stage': 'online_assessment'},
    ]


def test_final_stage_does_not_offer_noop_advance():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    client = app.test_client()
    _register_recruiter(client, 'final-stage-owner@example.com')
    job = _create_job(client, title='Engineer', slug='final-stage-engineer')
    application = _apply(client, job['public_slug'], 'final-stage@example.com')

    with app.app_context():
        get_job_service().get_by_id(job['id']).stage_order = ['voice_interview']
        get_application_service().get_by_id(application['id']).current_stage = 'voice_interview'

    response = client.get(f"/api/recruiter/jobs/{job['id']}/dashboard")
    assert response.status_code == 200
    actions = response.get_json()['candidates'][0]['available_actions']
    assert actions == [{'decision': 'reject', 'expected_stage': 'voice_interview'}]
