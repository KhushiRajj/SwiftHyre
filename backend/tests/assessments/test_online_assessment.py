from io import BytesIO

from swifthire import create_app


def _register_recruiter(client, email='recruiter@example.com'):
    response = client.post('/api/auth/register', json={
        'name': 'Recruiter One',
        'email': email,
        'password': 'secret123',
    })
    assert response.status_code == 201
    return response


def _publish_job(client, job_name='Senior Designer', slug='senior-designer'):
    response = client.post('/api/recruiter/jobs', json={
        'title': job_name,
        'description': 'Design product experiences.',
        'status': 'published',
        'public_slug': slug,
    })
    assert response.status_code == 201
    return response.get_json()


def _apply(client, slug='senior-designer', name='Jane Candidate', email='jane@example.com'):
    return client.post(
        f'/api/public/jobs/{slug}/applications',
        data={
            'name': name,
            'email': email,
            'cv': (BytesIO(b'%PDF-1.4\nBT\n(Resume) Tj\nET\n%%EOF'), 'resume.pdf', 'application/pdf'),
        },
        content_type='multipart/form-data',
    )


def test_email_invitation_and_quiz_flow_are_reviewed_and_scoped():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    client = app.test_client()

    _register_recruiter(client)
    job = _publish_job(client)
    application = _apply(client, slug=job['public_slug'])
    assert application.status_code == 201
    application_id = application.get_json()['id']

    decision = client.post(
        f"/api/recruiter/jobs/{job['id']}/applications/{application_id}/decisions",
        json={'decision': 'advance', 'expected_stage': 'online_assessment', 'idempotency_key': 'decision-1'},
    )
    assert decision.status_code == 201

    invite = client.post(
        f"/api/recruiter/jobs/{job['id']}/applications/{application_id}/invite",
        json={'stage': 'online_assessment'},
    )
    assert invite.status_code == 201
    invite_payload = invite.get_json()
    assert invite_payload['stage'] == 'online_assessment'
    assert invite_payload['token']
    assert invite_payload['status'] == 'sent'

    candidate_client = app.test_client()
    assessment = candidate_client.get(f"/api/assessments/{invite_payload['token']}")
    assert assessment.status_code == 200
    assert assessment.get_json()['questions']
    assert len(assessment.get_json()['questions']) == 10
    assert all('answer' not in question for question in assessment.get_json()['questions'])

    submission = candidate_client.post(
        f"/api/assessments/{invite_payload['token']}/submit",
        json={
            'answers': {
                'q1': 'A',
                'q2': 'B',
                'q3': 'C',
                'q4': 'D',
                'q5': 'A',
                'q6': 'B',
                'q7': 'C',
                'q8': 'D',
                'q9': 'A',
                'q10': 'B',
            }
        },
    )
    assert submission.status_code == 200
    assert submission.get_json()['status'] == 'submitted'
    assert isinstance(submission.get_json()['score'], int)
    assert 0 <= submission.get_json()['score'] <= 100

    repeat = candidate_client.get(f"/api/assessments/{invite_payload['token']}")
    assert repeat.status_code == 404

    missing = candidate_client.get('/api/assessments/not-a-real-token')
    assert missing.status_code == 404


def test_provider_failures_leave_retryable_status_and_review_gate():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    client = app.test_client()

    _register_recruiter(client, email='recruiter-two@example.com')
    job = _publish_job(client, job_name='Growth Lead', slug='growth-lead')
    application = _apply(client, slug=job['public_slug'], email='candidate-two@example.com')
    assert application.status_code == 201
    application_id = application.get_json()['id']

    decision = client.post(
        f"/api/recruiter/jobs/{job['id']}/applications/{application_id}/decisions",
        json={'decision': 'advance', 'expected_stage': 'online_assessment', 'idempotency_key': 'decision-2'},
    )
    assert decision.status_code == 201

    invite = client.post(
        f"/api/recruiter/jobs/{job['id']}/applications/{application_id}/invite",
        json={'stage': 'online_assessment', 'deliver': False},
    )
    assert invite.status_code == 201
    assert invite.get_json()['status'] == 'not_sent'

    candidate_client = app.test_client()
    assessment = candidate_client.get(f"/api/assessments/{invite.get_json()['token']}")
    assert assessment.status_code == 403

    review = client.get(f"/api/recruiter/jobs/{job['id']}/applications/{application_id}/assessments")
    assert review.status_code == 200
    body = review.get_json()
    assert len(body) >= 1
    assert body[0]['status'] in {'not_sent', 'pending_review'}
