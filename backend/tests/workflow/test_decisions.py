from io import BytesIO

from swifthire import create_app
from swifthire.applications.service import get_application_service
from swifthire.workflow.service import get_workflow_service


def test_recruiter_stage_decisions_are_scoped_and_idempotent():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    client = app.test_client()

    recruiter = client.post('/api/auth/register', json={'name': 'Recruiter A', 'email': 'a@example.com', 'password': 'secret123'})
    assert recruiter.status_code == 201

    other = client.post('/api/auth/register', json={'name': 'Recruiter B', 'email': 'b@example.com', 'password': 'secret123'})
    assert other.status_code == 201

    job = client.post('/api/recruiter/jobs', json={
        'title': 'Senior Designer',
        'description': 'Design product experiences.',
        'status': 'published',
        'public_slug': 'senior-designer',
    })
    assert job.status_code == 201
    job_data = job.get_json()

    config = client.patch(f"/api/recruiter/jobs/{job_data['id']}", json={
        'stage_order': ['online_assessment', 'coding_assessment', 'voice_interview'],
        'recommendation_threshold': 80,
    })
    assert config.status_code == 200
    assert config.get_json()['stage_order'] == ['online_assessment', 'coding_assessment', 'voice_interview']
    assert config.get_json()['recommendation_threshold'] == 80

    application = client.post(
        f"/api/public/jobs/{job_data['public_slug']}/applications",
        data={
            'name': 'Jane Candidate',
            'email': 'jane@example.com',
            'cv': (BytesIO(b'%PDF-1.4\nBT\n(Resume) Tj\nET\n%%EOF'), 'resume.pdf', 'application/pdf'),
        },
        content_type='multipart/form-data',
    )
    assert application.status_code == 201
    application_id = application.get_json()['id']

    first = client.post(
        f"/api/recruiter/jobs/{job_data['id']}/applications/{application_id}/decisions",
        json={'decision': 'advance', 'expected_stage': 'online_assessment', 'idempotency_key': 'decision-1'},
    )
    assert first.status_code == 201
    assert first.get_json()['decision'] == 'advance'
    with app.app_context():
        assert get_application_service().get_by_id(application_id).current_stage == 'coding_assessment'

    repeat = client.post(
        f"/api/recruiter/jobs/{job_data['id']}/applications/{application_id}/decisions",
        json={'decision': 'advance', 'expected_stage': 'online_assessment', 'idempotency_key': 'decision-1'},
    )
    assert repeat.status_code == 200
    assert repeat.get_json()['id'] == first.get_json()['id']

    invalid = client.post(
        f"/api/recruiter/jobs/{job_data['id']}/applications/{application_id}/decisions",
        json={'decision': 'advance', 'expected_stage': 'online_assessment', 'idempotency_key': 'decision-2'},
    )
    assert invalid.status_code == 409

    other_client = app.test_client()
    other_client.post('/api/auth/register', json={'name': 'Recruiter C', 'email': 'c@example.com', 'password': 'secret123'})
    denied = other_client.post(
        f"/api/recruiter/jobs/{job_data['id']}/applications/{application_id}/decisions",
        json={'decision': 'reject', 'expected_stage': 'online_assessment', 'idempotency_key': 'decision-3'},
    )
    assert denied.status_code == 403

    threshold = client.post(
        f"/api/recruiter/jobs/{job_data['id']}/applications/{application_id}/decisions",
        json={'decision': 'advance', 'expected_stage': 'coding_assessment', 'idempotency_key': 'decision-4', 'recommendation_score': 70},
    )
    assert threshold.status_code == 201
    assert threshold.get_json()['decision'] == 'advance'
    assert threshold.get_json()['status'] == 'recommendation'


def test_list_decisions_for_application_returns_created_decisions_in_order():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    client = app.test_client()
    client.post('/api/auth/register', json={
        'name': 'Recruiter',
        'email': 'history@example.com',
        'password': 'secret123',
    })
    job = client.post('/api/recruiter/jobs', json={
        'title': 'Engineer',
        'description': 'Build reliable software.',
        'status': 'published',
        'public_slug': 'history-engineer',
    }).get_json()

    def apply(email: str):
        response = client.post(
            f"/api/public/jobs/{job['public_slug']}/applications",
            data={
                'name': 'Candidate',
                'email': email,
                'cv': (BytesIO(b'%PDF-1.4\n%%EOF'), 'resume.pdf', 'application/pdf'),
            },
            content_type='multipart/form-data',
        )
        assert response.status_code == 201
        return response.get_json()

    first_application = apply('first-history@example.com')
    second_application = apply('second-history@example.com')

    first_decision = client.post(
        f"/api/recruiter/jobs/{job['id']}/applications/{first_application['id']}/decisions",
        json={'decision': 'advance', 'expected_stage': 'online_assessment'},
    ).get_json()
    second_decision = client.post(
        f"/api/recruiter/jobs/{job['id']}/applications/{first_application['id']}/decisions",
        json={'decision': 'reject', 'expected_stage': 'coding_assessment'},
    ).get_json()
    client.post(
        f"/api/recruiter/jobs/{job['id']}/applications/{second_application['id']}/decisions",
        json={'decision': 'reject', 'expected_stage': 'online_assessment'},
    )

    with app.app_context():
        decisions = get_workflow_service().list_decisions_for_application(first_application['id'])

    assert [decision.id for decision in decisions] == [first_decision['id'], second_decision['id']]
    assert [decision.created_at for decision in decisions] == sorted(
        decision.created_at for decision in decisions
    )
