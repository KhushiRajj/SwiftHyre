from __future__ import annotations

from flask import Blueprint, jsonify, request, session

from .service import get_job_service

jobs_bp = Blueprint('jobs', __name__, url_prefix='/api')


def _require_recruiter():
    recruiter_id = session.get('recruiter_id')
    if not recruiter_id:
        return None
    return recruiter_id


@jobs_bp.post('/recruiter/jobs')
def create_job():
    service = get_job_service()
    recruiter_id = _require_recruiter()
    if recruiter_id is None:
        return jsonify({'error': 'authentication required'}), 401

    data = request.get_json(silent=True) or {}
    title = (data.get('title') or '').strip()
    description = (data.get('description') or '').strip()
    if not title or not description:
        return jsonify({'error': 'title and description are required'}), 400

    status = data.get('status', 'draft')
    public_slug = (data.get('public_slug') or None)
    job = service.create_job(recruiter_id, title, description, status=status, public_slug=public_slug)
    response = jsonify(job.to_dict())
    response.status_code = 201
    return response


@jobs_bp.get('/recruiter/jobs')
def list_jobs():
    service = get_job_service()
    recruiter_id = _require_recruiter()
    if recruiter_id is None:
        return jsonify({'error': 'authentication required'}), 401

    jobs = service.list_for_recruiter(recruiter_id)
    return jsonify([job.to_dict() for job in jobs])


@jobs_bp.get('/recruiter/jobs/<job_id>')
def get_job(job_id: str):
    service = get_job_service()
    recruiter_id = _require_recruiter()
    if recruiter_id is None:
        return jsonify({'error': 'authentication required'}), 401

    job = service.get_by_id(job_id)
    if job is None or job.recruiter_id != recruiter_id:
        return jsonify({'error': 'forbidden'}), 403

    return jsonify(job.to_dict())


@jobs_bp.patch('/recruiter/jobs/<job_id>')
def update_job(job_id: str):
    service = get_job_service()
    recruiter_id = _require_recruiter()
    if recruiter_id is None:
        return jsonify({'error': 'authentication required'}), 401

    data = request.get_json(silent=True) or {}
    try:
        job = service.update_job(job_id, recruiter_id, **data)
    except ValueError:
        return jsonify({'error': 'forbidden'}), 403

    return jsonify(job.to_dict())


@jobs_bp.get('/public/jobs/<slug>')
def public_job(slug: str):
    service = get_job_service()
    job = service.get_by_slug(slug)
    if job is None or job.status != 'published':
        return jsonify({'error': 'job not found'}), 404

    return jsonify(job.to_dict())
