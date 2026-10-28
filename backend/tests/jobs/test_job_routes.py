from swifthire import create_app


def test_job_routes_and_public_job_view():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    client = app.test_client()

    register = client.post('/api/auth/register', json={
        'name': 'Alice Recruiter',
        'email': 'alice@example.com',
        'password': 'secret123',
    })
    assert register.status_code == 201

    created = client.post('/api/recruiter/jobs', json={
        'title': 'Senior Product Designer',
        'description': 'Design product experiences.',
        'status': 'draft',
    })
    assert created.status_code == 201
    data = created.get_json()
    assert data['title'] == 'Senior Product Designer'
    assert data['description'] == 'Design product experiences.'
    assert data['status'] == 'draft'
    assert data['public_slug']

    listed = client.get('/api/recruiter/jobs')
    assert listed.status_code == 200
    assert len(listed.get_json()) == 1

    published = client.patch(f"/api/recruiter/jobs/{data['id']}", json={
        'status': 'published',
        'public_slug': data['public_slug'],
    })
    assert published.status_code == 200
    assert published.get_json()['status'] == 'published'

    public_view = client.get(f"/api/public/jobs/{data['public_slug']}")
    assert public_view.status_code == 200
    assert public_view.get_json()['title'] == 'Senior Product Designer'

    other_client = app.test_client()
    other_client.post('/api/auth/register', json={
        'name': 'Other Recruiter',
        'email': 'other@example.com',
        'password': 'secret123',
    })
    owner_denied = other_client.get(f"/api/recruiter/jobs/{data['id']}")
    assert owner_denied.status_code == 403

    closed = client.patch(f"/api/recruiter/jobs/{data['id']}", json={'status': 'closed'})
    assert closed.status_code == 200
    hidden = client.get(f"/api/public/jobs/{data['public_slug']}")
    assert hidden.status_code == 404

    missing = client.get('/api/public/jobs/missing-slug')
    assert missing.status_code == 404
