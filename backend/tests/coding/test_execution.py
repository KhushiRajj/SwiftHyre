import json
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from threading import Event, Lock
from urllib.error import HTTPError

from swifthire import create_app
from swifthire.applications.service import get_application_service
from swifthire.assessments.service import get_assessment_service
from swifthire.coding.models import CodingTestCase
from swifthire.coding.runner import CodeRunner, ExecutionResult
from swifthire.coding.service import CodingChallengeService


class FakeRunner:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def run(self, source, language, stdin, timeout_seconds):
        self.calls.append((source, language, stdin, timeout_seconds))
        if self.results:
            return self.results.pop(0)
        raise AssertionError('unexpected code execution')


class FakeHttpResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload).encode('utf-8')


def _register_recruiter(client, email: str):
    response = client.post('/api/auth/register', json={
        'name': 'Recruiter',
        'email': email,
        'password': 'secret123',
    })
    assert response.status_code == 201
    return response.get_json()['user']


def _create_job(client):
    response = client.post('/api/recruiter/jobs', json={
        'title': 'Engineer',
        'description': 'Build reliable code.',
        'status': 'published',
        'public_slug': 'engineer',
    })
    assert response.status_code == 201
    return response.get_json()


def _apply(client, slug='engineer'):
    response = client.post(
        f'/api/public/jobs/{slug}/applications',
        data={
            'name': 'Jane Candidate',
            'email': 'jane@example.com',
            'cv': (BytesIO(b'%PDF-1.4\n%%EOF'), 'resume.pdf', 'application/pdf'),
        },
        content_type='multipart/form-data',
    )
    assert response.status_code == 201
    return response.get_json()


def _coding_token(app, application_id, job_id):
    with app.app_context():
        application = get_application_service().get_by_id(application_id)
        application.current_stage = 'coding_assessment'
        assessment = get_assessment_service().create_assessment(
            application_id,
            job_id,
            'coding_assessment',
        )
        assessment.status = 'pending_review'
        return assessment.token


def _create_challenge(client, job_id):
    response = client.post(f'/api/recruiter/jobs/{job_id}/coding-challenges', json={
        'title': 'Add numbers',
        'prompt': 'Print the sum of two integers from standard input.',
        'allowed_languages': ['python'],
        'public_test_cases': [{'input': '1\n2', 'expected_output': '3'}],
        'private_test_cases': [
            {'input': '1\n2', 'expected_output': '3'},
            {'input': '5\n6', 'expected_output': '11'},
        ],
    })
    assert response.status_code == 201
    return response.get_json()


def test_missing_provider_credentials_are_unavailable_not_simulated_success(monkeypatch):
    monkeypatch.delenv('ONLINECOMPILER_API_KEY', raising=False)

    result = CodeRunner().run('print("anything")', 'python', '', 1)

    assert result.status == 'unavailable'
    assert result.exit_code is None


def test_runner_sends_code_and_input_to_onlinecompiler_with_server_key(monkeypatch):
    observed = {}

    def fake_urlopen(request, timeout):
        observed['url'] = request.full_url
        observed['authorization'] = request.get_header('Authorization')
        observed['timeout'] = timeout
        observed['payload'] = json.loads(request.data.decode('utf-8'))
        return FakeHttpResponse({
            'output': '3\n',
            'error': '',
            'exit_code': 0,
            'time': 0.02,
            'total': 0.04,
        })

    monkeypatch.setattr('urllib.request.urlopen', fake_urlopen)
    runner = CodeRunner(api_key='server-only-key')

    result = runner.run('print(1 + 2)', 'python', '1\n2', 4)

    assert result.status == 'completed'
    assert result.stdout == '3\n'
    assert result.exit_code == 0
    assert observed == {
        'url': 'https://api.onlinecompiler.io/api/run-code-sync/',
        'authorization': 'server-only-key',
        'timeout': 14,
        'payload': {
            'compiler': 'python-3.14',
            'code': 'print(1 + 2)',
            'input': '1\n2',
            'time_limit': 4,
        },
    }


def test_private_cases_are_run_and_only_aggregate_score_is_returned():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    client = app.test_client()
    _register_recruiter(client, 'execution-owner@example.com')
    job = _create_job(client)
    application = _apply(client)
    token = _coding_token(app, application['id'], job['id'])
    runner = FakeRunner([
        ExecutionResult('completed', '3\n', '', 15, 0),
        ExecutionResult('completed', '11\n', '', 13, 0),
    ])
    app.extensions['coding_service'] = CodingChallengeService(runner=runner)
    challenge = _create_challenge(client, job['id'])

    response = client.post(
        f"/api/public/coding-challenges/{challenge['id']}/submissions",
        json={
            'assessment_token': token,
            'language': 'python',
            'source': 'read two numbers and add them',
        },
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload['score'] == 100
    assert payload['status'] == 'completed'
    assert len(runner.calls) == 2
    assert [call[2] for call in runner.calls] == ['1\n2', '5\n6']
    assert 'stdout' not in payload
    assert 'stderr' not in payload
    assert 'source' not in payload
    assert 'private_test_cases' not in payload


def test_timeout_has_no_candidate_score_and_can_retry():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    client = app.test_client()
    _register_recruiter(client, 'execution-retry@example.com')
    job = _create_job(client)
    application = _apply(client)
    token = _coding_token(app, application['id'], job['id'])
    runner = FakeRunner([
        ExecutionResult('timeout', '', 'execution timed out', None, 124),
        ExecutionResult('completed', '3\n', '', 12, 0),
        ExecutionResult('completed', '11\n', '', 10, 0),
    ])
    app.extensions['coding_service'] = CodingChallengeService(runner=runner)
    challenge = _create_challenge(client, job['id'])
    request_payload = {
        'assessment_token': token,
        'language': 'python',
        'source': 'read two numbers and add them',
    }
    url = f"/api/public/coding-challenges/{challenge['id']}/submissions"

    failed = client.post(url, json=request_payload)
    assert failed.status_code == 201
    assert failed.get_json()['status'] == 'timeout'
    assert 'score' not in failed.get_json()

    retried = client.post(url, json=request_payload)
    assert retried.status_code == 200
    assert retried.get_json()['score'] == 100
    assert retried.get_json()['id'] == failed.get_json()['id']

    duplicate = client.post(url, json=request_payload)
    assert duplicate.get_json()['id'] == retried.get_json()['id']
    assert len(runner.calls) == 3


def test_submission_requires_an_active_coding_stage_token():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    client = app.test_client()
    _register_recruiter(client, 'execution-token@example.com')
    job = _create_job(client)
    _apply(client)
    app.extensions['coding_service'] = CodingChallengeService(
        runner=FakeRunner([ExecutionResult('completed', 'ok', '', 1, 0)])
    )
    challenge = _create_challenge(client, job['id'])

    response = client.post(
        f"/api/public/coding-challenges/{challenge['id']}/submissions",
        json={'language': 'python', 'source': 'print("ok")'},
    )

    assert response.status_code == 401
    assert 'assessment token' in response.get_json()['error'].lower()


def test_submission_rejects_a_token_for_a_stage_the_application_has_not_reached():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    client = app.test_client()
    _register_recruiter(client, 'execution-wrong-stage@example.com')
    job = _create_job(client)
    application = _apply(client)
    with app.app_context():
        assessment = get_assessment_service().create_assessment(
            application['id'],
            job['id'],
            'coding_assessment',
        )
        assessment.status = 'pending_review'
    runner = FakeRunner([
        ExecutionResult('completed', 'ok', '', 1, 0),
        ExecutionResult('completed', 'ok', '', 1, 0),
    ])
    app.extensions['coding_service'] = CodingChallengeService(runner=runner)
    challenge = _create_challenge(client, job['id'])

    response = client.post(
        f"/api/public/coding-challenges/{challenge['id']}/submissions",
        json={
            'assessment_token': assessment.token,
            'language': 'python',
            'source': 'print("ok")',
        },
    )

    assert response.status_code == 403
    assert runner.calls == []


def test_rejected_application_cannot_use_an_outstanding_coding_token():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    client = app.test_client()
    _register_recruiter(client, 'execution-rejected@example.com')
    job = _create_job(client)
    application = _apply(client)
    token = _coding_token(app, application['id'], job['id'])
    runner = FakeRunner([
        ExecutionResult('completed', '3\n', '', 1, 0),
        ExecutionResult('completed', '11\n', '', 1, 0),
    ])
    app.extensions['coding_service'] = CodingChallengeService(runner=runner)
    challenge = _create_challenge(client, job['id'])

    decision = client.post(
        f"/api/recruiter/jobs/{job['id']}/applications/{application['id']}/decisions",
        json={'decision': 'reject', 'expected_stage': 'coding_assessment'},
    )
    assert decision.status_code == 201

    response = client.post(
        f"/api/public/coding-challenges/{challenge['id']}/submissions",
        json={
            'assessment_token': token,
            'language': 'python',
            'source': 'print("ok")',
        },
    )

    assert response.status_code == 403
    assert runner.calls == []


def test_provider_authentication_error_is_unavailable_and_candidate_safe(monkeypatch):
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'ONLINECOMPILER_API_KEY': 'invalid-key',
    })
    client = app.test_client()
    _register_recruiter(client, 'execution-provider-error@example.com')
    job = _create_job(client)
    application = _apply(client)
    token = _coding_token(app, application['id'], job['id'])
    challenge = _create_challenge(client, job['id'])

    def reject_authentication(_request, timeout):
        raise HTTPError('https://api.onlinecompiler.io/api/run-code-sync/', 401, 'unauthorized', {}, None)

    monkeypatch.setattr('urllib.request.urlopen', reject_authentication)
    response = client.post(
        f"/api/public/coding-challenges/{challenge['id']}/submissions",
        json={
            'assessment_token': token,
            'language': 'python',
            'source': 'print("ok")',
        },
    )

    payload = response.get_json()
    assert response.status_code == 201
    assert payload['status'] == 'unavailable'
    assert 'provider' in payload['message'].lower()
    assert 'score' not in payload
    assert 'invalid-key' not in response.get_data(as_text=True)


def test_concurrent_retries_share_one_submission_and_provider_run():
    first_run_started = Event()
    release_first_run = Event()
    duplicate_provider_run = Event()
    runner_lock = Lock()
    active_runs = 0
    call_count = 0

    class BlockingRunner:
        def run(self, source, language, stdin, timeout_seconds):
            nonlocal active_runs, call_count
            with runner_lock:
                call_count += 1
                current_call = call_count
                if active_runs:
                    duplicate_provider_run.set()
                active_runs += 1
            if current_call == 1:
                first_run_started.set()
                release_first_run.wait(timeout=2)
            with runner_lock:
                active_runs -= 1
            return ExecutionResult('completed', 'ok', '', 1, 0)

    service = CodingChallengeService(runner=BlockingRunner())
    challenge = service.create_challenge(
        'job-id',
        'recruiter-id',
        'Concurrency challenge',
        'Return ok.',
        ['python'],
        private_test_cases=[
            {'input': 'first', 'expected_output': 'ok'},
            {'input': 'second', 'expected_output': 'ok'},
        ],
    )

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(service.create_submission, challenge.id, 'application-id', 'python', 'source')
        assert first_run_started.wait(timeout=1)
        second_started = Event()

        def retry():
            second_started.set()
            return service.create_submission(challenge.id, 'application-id', 'python', 'source')

        second = executor.submit(retry)
        assert second_started.wait(timeout=1)
        duplicate_run_seen = duplicate_provider_run.wait(timeout=0.1)
        release_first_run.set()
        first_submission = first.result(timeout=2)
        second_submission = second.result(timeout=2)

    assert not duplicate_run_seen
    assert first_submission.id == second_submission.id
    assert call_count == 2
    assert len(service.list_submissions(challenge.id)) == 1


def test_runner_rejects_unsupported_language_and_limits_before_provider_call():
    runner = FakeRunner([])
    code_runner = CodeRunner(provider=runner)

    unsupported = code_runner.run('source', 'unknown', '', 1)
    oversized = code_runner.run('x' * 100001, 'python', '', 1)

    assert unsupported.status == 'unavailable'
    assert oversized.status == 'invalid'
    assert runner.calls == []


def test_recruiter_can_review_owned_candidate_score_without_source_or_hidden_data():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    owner_client = app.test_client()
    _register_recruiter(owner_client, 'results-owner@example.com')
    job = _create_job(owner_client)
    application = _apply(owner_client)
    token = _coding_token(app, application['id'], job['id'])
    runner = FakeRunner([
        ExecutionResult('completed', '3\n', '', 10, 0),
        ExecutionResult('completed', '11\n', '', 10, 0),
    ])
    app.extensions['coding_service'] = CodingChallengeService(runner=runner)
    challenge = _create_challenge(owner_client, job['id'])
    submitted = owner_client.post(
        f"/api/public/coding-challenges/{challenge['id']}/submissions",
        json={
            'assessment_token': token,
            'language': 'python',
            'source': 'candidate secret source',
        },
    )
    assert submitted.status_code == 201

    response = owner_client.get(
        f"/api/recruiter/jobs/{job['id']}/coding-challenges/{challenge['id']}/submissions"
    )

    assert response.status_code == 200
    result = response.get_json()[0]
    assert result['candidate_name'] == 'Jane Candidate'
    assert result['score'] == 100
    assert result['status'] == 'completed'
    assert 'source' not in result
    assert 'candidate secret source' not in response.get_data(as_text=True)
    assert '5\\n6' not in response.get_data(as_text=True)


def test_coding_results_are_not_visible_to_another_recruiter():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    owner_client = app.test_client()
    other_client = app.test_client()
    _register_recruiter(owner_client, 'results-owner-scope@example.com')
    _register_recruiter(other_client, 'results-other@example.com')
    job = _create_job(owner_client)

    response = other_client.get(
        f"/api/recruiter/jobs/{job['id']}/coding-challenges/not-a-challenge/submissions"
    )

    assert response.status_code == 403
