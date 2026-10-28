from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request, session

from .service import get_recruiter_service


auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.post('/register')
def register():
    service = get_recruiter_service()
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''

    if not name or not email or not password:
        return jsonify({'error': 'name, email and password are required'}), 400

    normalized_email = email.lower()
    if service.authenticate(normalized_email, password) is not None:
        return jsonify({'error': 'email already registered'}), 409

    try:
        recruiter = service.create_recruiter(name, normalized_email, password)
    except ValueError:
        return jsonify({'error': 'email already registered'}), 409

    session.clear()
    session['recruiter_id'] = recruiter.id
    response = jsonify({'user': recruiter.to_public_dict()})
    response.status_code = 201
    return response


@auth_bp.post('/login')
def login():
    service = get_recruiter_service()
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or not password:
        return jsonify({'error': 'email and password are required'}), 400

    recruiter = service.authenticate(email, password)
    if recruiter is None:
        return jsonify({'error': 'invalid credentials'}), 401

    session.clear()
    session['recruiter_id'] = recruiter.id
    return jsonify({'user': recruiter.to_public_dict()})


@auth_bp.post('/logout')
def logout():
    session.clear()
    return jsonify({'status': 'ok'})


@auth_bp.get('/me')
def me():
    service = get_recruiter_service()
    recruiter_id = session.get('recruiter_id')
    if not recruiter_id:
        return jsonify({'error': 'authentication required'}), 401

    recruiter = service.get_by_id(recruiter_id)
    if recruiter is None:
        session.clear()
        return jsonify({'error': 'authentication required'}), 401

    return jsonify(recruiter.to_public_dict())
