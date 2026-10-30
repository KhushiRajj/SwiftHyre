from swifthire import create_app


def test_auth_routes_work_for_register_login_me_and_logout():
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'SESSION_COOKIE_HTTPONLY': True,
        'SESSION_COOKIE_SAMESITE': 'Lax',
    })
    client = app.test_client()

    register = client.post(
        '/api/auth/register',
        json={'name': 'Alice Recruiter', 'email': 'ALICE@example.com', 'password': 'secret123'},
    )
    assert register.status_code == 201
    payload = register.get_json()
    assert payload['user']['email'] == 'alice@example.com'
    assert payload['user']['name'] == 'Alice Recruiter'

    cookie_header = register.headers.get('Set-Cookie', '')
    assert 'HttpOnly' in cookie_header
    assert 'SameSite=Lax' in cookie_header

    duplicate = client.post(
        '/api/auth/register',
        json={'name': 'Alice Recruiter', 'email': 'alice@example.com', 'password': 'secret123'},
    )
    assert duplicate.status_code == 409

    lost = client.get('/api/auth/me')
    assert lost.status_code == 200

    bad_login = client.post(
        '/api/auth/login',
        json={'email': 'alice@example.com', 'password': 'wrong-password'},
    )
    assert bad_login.status_code == 401

    me = client.get('/api/auth/me')
    assert me.status_code == 200
    assert me.get_json()['email'] == 'alice@example.com'

    unauth = app.test_client().get('/api/auth/me')
    assert unauth.status_code == 401

    logout = client.post('/api/auth/logout')
    assert logout.status_code == 200
    assert logout.get_json()['status'] == 'ok'

    after_logout = client.get('/api/auth/me')
    assert after_logout.status_code == 401
