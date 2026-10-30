from io import BytesIO

from swifthire import create_app


def test_public_application_submission_and_validation_rules():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    client = app.test_client()

    recruiter = client.post(
        '/api/auth/register',
        json={'name': 'Alice Recruiter', 'email': 'alice@example.com', 'password': 'secret123'},
    )
    assert recruiter.status_code == 201

    job = client.post(
        '/api/recruiter/jobs',
        json={'title': 'Senior Product Designer', 'description': 'Design great product experiences.', 'status': 'published', 'public_slug': 'senior-product-designer'},
    )
    assert job.status_code == 201
    created = job.get_json()

    pdf_bytes = b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF'

    valid = client.post(
        f"/api/public/jobs/{created['public_slug']}/applications",
        data={
            'name': 'Jane Candidate',
            'email': 'jane@example.com',
            'cv': (BytesIO(pdf_bytes), 'resume.pdf', 'application/pdf'),
        },
        content_type='multipart/form-data',
    )
    assert valid.status_code == 201
    payload = valid.get_json()
    assert payload['applicant_name'] == 'Jane Candidate'
    assert payload['email'] == 'jane@example.com'
    assert payload['cv']['content_type'] == 'application/pdf'
    assert payload['cv']['size_bytes'] == len(pdf_bytes)

    draft_job = client.post(
        '/api/recruiter/jobs',
        json={'title': 'Hidden Role', 'description': 'Not visible yet.', 'status': 'draft', 'public_slug': 'hidden-role'},
    )
    assert draft_job.status_code == 201

    unpublished = client.post(
        '/api/public/jobs/hidden-role/applications',
        data={
            'name': 'Other Candidate',
            'email': 'other@example.com',
            'cv': (BytesIO(pdf_bytes), 'resume.pdf', 'application/pdf'),
        },
        content_type='multipart/form-data',
    )
    assert unpublished.status_code == 404

    bad_file = client.post(
        f"/api/public/jobs/{created['public_slug']}/applications",
        data={
            'name': 'Bad Candidate',
            'email': 'bad@example.com',
            'cv': (BytesIO(b'not a pdf'), 'resume.txt', 'text/plain'),
        },
        content_type='multipart/form-data',
    )
    assert bad_file.status_code == 400

    large = client.post(
        f"/api/public/jobs/{created['public_slug']}/applications",
        data={
            'name': 'Large Candidate',
            'email': 'large@example.com',
            'cv': (BytesIO(b'a' * (10 * 1024 * 1024 + 1)), 'large.pdf', 'application/pdf'),
        },
        content_type='multipart/form-data',
    )
    assert large.status_code == 400
