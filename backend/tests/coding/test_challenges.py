from swifthire import create_app


def _register_recruiter(client, email: str):
    response = client.post('/api/auth/register', json={
        'name': 'Recruiter',
        'email': email,
        'password': 'secret123',
    })
    assert response.status_code == 201
    return response.get_json()['user']


def _create_job(client, title='Frontend Engineer', slug='frontend-engineer', status='published'):
    response = client.post('/api/recruiter/jobs', json={
        'title': title,
        'description': 'Build product experiences.',
        'status': status,
        'public_slug': slug,
    })
    assert response.status_code == 201
    return response.get_json()


def test_recruiter_can_create_challenge_with_private_tests():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    client = app.test_client()
    _register_recruiter(client, 'challenge-owner@example.com')
    job = _create_job(client)

    payload = {
        'title': 'React filter challenge',
        'prompt': 'Write a function that filters active users from a list of records.',
        'allowed_languages': ['python', 'javascript'],
        'public_test_cases': [{'input': '[]', 'expected_output': '[]'}],
        'private_test_cases': [
            {'input': '[{"active": true},{"active": false}]', 'expected_output': '[{"active": true}]'},
            {'input': '[]', 'expected_output': '[]'},
        ],
    }

    response = client.post(f"/api/recruiter/jobs/{job['id']}/coding-challenges", json=payload)
    assert response.status_code == 201
    body = response.get_json()
    assert body['title'] == 'React filter challenge'
    assert body['allowed_languages'] == ['python', 'javascript']
    assert body['private_test_cases']


def test_cannot_create_challenge_without_prompt_or_private_tests():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    client = app.test_client()
    _register_recruiter(client, 'challenge-invalid@example.com')
    job = _create_job(client)

    response = client.post(f"/api/recruiter/jobs/{job['id']}/coding-challenges", json={
        'title': 'Missing prompt',
        'allowed_languages': ['python'],
        'public_test_cases': [{'input': '[]', 'expected_output': '[]'}],
        'private_test_cases': [],
    })
    assert response.status_code == 400
    assert 'prompt' in response.get_json()['error'].lower()


def test_challenge_rejects_non_list_language_configuration():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    client = app.test_client()
    _register_recruiter(client, 'challenge-languages@example.com')
    job = _create_job(client)

    response = client.post(f"/api/recruiter/jobs/{job['id']}/coding-challenges", json={
        'title': 'Invalid language config',
        'prompt': 'Print input.',
        'allowed_languages': 'python',
        'private_test_cases': [{'input': '', 'expected_output': ''}],
    })

    assert response.status_code == 400
    assert 'allowed languages' in response.get_json()['error'].lower()


def test_candidate_receives_only_public_challenge_data():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    client = app.test_client()
    _register_recruiter(client, 'challenge-candidate@example.com')
    job = _create_job(client, title='Data Analyst', slug='data-analyst')

    challenge = client.post(f"/api/recruiter/jobs/{job['id']}/coding-challenges", json={
        'title': 'String parser',
        'prompt': 'Return the total count of digits in the input string.',
        'allowed_languages': ['python'],
        'public_test_cases': [{'input': 'abc123', 'expected_output': '3'}],
        'private_test_cases': [{'input': 'a1b2c3', 'expected_output': 'hidden-answer'}],
    }).get_json()

    response = client.get(f"/api/public/jobs/{job['public_slug']}/coding-challenges")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload[0]['title'] == 'String parser'
    assert payload[0]['prompt'] == 'Return the total count of digits in the input string.'
    assert payload[0]['allowed_languages'] == ['python']
    assert 'private_test_cases' not in payload[0]
    assert payload[0]['public_test_cases'] == [{'input': 'abc123', 'expected_output': '3'}]
    assert 'a1b2c3' not in str(payload[0])
    assert 'hidden-answer' not in str(payload[0])


def test_candidate_submission_rejects_invalid_or_oversized_payloads():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
    client = app.test_client()
    _register_recruiter(client, 'challenge-submit@example.com')
    job = _create_job(client)
    challenge = client.post(f"/api/recruiter/jobs/{job['id']}/coding-challenges", json={
        'title': 'Small task',
        'prompt': 'Write a function.',
        'allowed_languages': ['python'],
        'public_test_cases': [{'input': '1', 'expected_output': '1'}],
        'private_test_cases': [{'input': '1', 'expected_output': '1'}],
    }).get_json()

    response = client.post(f"/api/public/coding-challenges/{challenge['id']}/submissions", json={
        'language': 'ruby',
        'source': 'print(1)',
    })
    assert response.status_code == 400
    assert 'language' in response.get_json()['error'].lower()

    oversized = 'x' * 200000
    response = client.post(f"/api/public/coding-challenges/{challenge['id']}/submissions", json={
        'language': 'python',
        'source': oversized,
    })
    assert response.status_code == 400
    assert 'too large' in response.get_json()['error'].lower()
