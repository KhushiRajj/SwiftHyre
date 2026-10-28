from __future__ import annotations

from io import BytesIO

from flask import Blueprint, jsonify, request

from ..jobs.service import get_job_service
from ..storage.base import StorageError
from .service import get_application_service

applications_bp = Blueprint('applications', __name__, url_prefix='/api')


@applications_bp.get('/public/jobs/<slug>/applications')
def list_public_applications(slug: str):
    return jsonify({'error': 'job not found'}), 404


@applications_bp.post('/public/jobs/<slug>/applications')
def submit_public_application(slug: str):
    job_service = get_job_service()
    job = job_service.get_by_slug(slug)
    if job is None or job.status != 'published':
        return jsonify({'error': 'job not found'}), 404

    name = (request.form.get('name') or '').strip()
    email = (request.form.get('email') or '').strip()
    uploaded_file = request.files.get('cv')

    if not name or not email or uploaded_file is None:
        return jsonify({'error': 'name, email and cv are required'}), 400

    file_bytes = uploaded_file.read()
    if not file_bytes:
        return jsonify({'error': 'Please upload a PDF file under 10 MiB.'}), 400

    file_name = (uploaded_file.filename or '').lower()
    content_type = (uploaded_file.mimetype or 'application/pdf').lower()
    is_pdf = file_name.endswith('.pdf') or content_type == 'application/pdf'
    if not is_pdf or len(file_bytes) > 10 * 1024 * 1024:
        return jsonify({'error': 'Please upload a PDF file under 10 MiB.'}), 400

    service = get_application_service()
    try:
        application = service.submit_application(job, name, email, BytesIO(file_bytes), content_type)
    except (StorageError, ValueError) as exc:
        return jsonify({'error': str(exc)}), 400

    response = jsonify({
        'id': application.id,
        'job_id': application.job_id,
        'applicant_name': application.applicant_name,
        'email': application.email,
        'cv': application.cv.to_dict(),
        'status': application.status,
        'created_at': application.created_at,
    })
    response.status_code = 201
    return response
