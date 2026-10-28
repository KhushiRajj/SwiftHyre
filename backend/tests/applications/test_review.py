from io import BytesIO

from swifthire import create_app


def test_recruiter_application_review_is_owner_only_and_shows_screening_evidence():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    client = app.test_client()

    recruiter_a = client.post('/api/auth/register', json={'name': 'Recruiter A', 'email': 'a@example.com', 'password': 'secret123'})
    recruiter_b = client.post('/api/auth/register', json={'name': 'Recruiter B', 'email': 'b@example.com', 'password': 'secret123'})
    assert recruiter_a.status_code == 201
    assert recruiter_b.status_code == 201

    created_job = client.post('/api/recruiter/jobs', json={'title': 'Senior Product Designer', 'description': 'Lead design strategy.', 'status': 'published', 'public_slug': 'design-chief'})
    assert created_job.status_code == 201
    job = created_job.get_json()

    candidate = client.post(
        f"/api/public/jobs/{job['public_slug']}/applications",
        data={
            'name': 'Jane Candidate',
            'email': 'jane@example.com',
            'cv': (BytesIO(b'%PDF-1.4\nBT\n(Resume) Tj\nET\n%%EOF'), 'resume.pdf', 'application/pdf'),
        },
        content_type='multipart/form-data',
    )
    assert candidate.status_code == 201
    application = candidate.get_json()

    list_as_owner = client.get(f"/api/recruiter/jobs/{job['id']}/applications")
    assert list_as_owner.status_code == 200
    assert len(list_as_owner.get_json()) == 1
    assert list_as_owner.get_json()[0]['status'] == 'pending'

    detail_as_owner = client.get(f"/api/recruiter/jobs/{job['id']}/applications/{application['id']}")
    assert detail_as_owner.status_code == 200
    body = detail_as_owner.get_json()
    assert body['applicant_name'] == 'Jane Candidate'
    assert body['screening']['summary'] == 'Strong fit for the role.'
    assert body['screening']['criteria'][0]['name'] == 'Product leadership'

    other_client = app.test_client()
    other_client.post('/api/auth/register', json={'name': 'Recruiter C', 'email': 'c@example.com', 'password': 'secret123'})
    denied = other_client.get(f"/api/recruiter/jobs/{job['id']}/applications")
    assert denied.status_code == 403

    public = app.test_client().get(f"/api/public/jobs/{job['public_slug']}/applications")
    assert public.status_code == 404
