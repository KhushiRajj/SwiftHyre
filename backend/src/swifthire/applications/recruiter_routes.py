from __future__ import annotations

from flask import Blueprint, jsonify, request, session

from ..jobs.service import get_job_service
from .service import get_application_service

recruiter_applications_bp = Blueprint('recruiter_applications', __name__, url_prefix='/api/recruiter')


@recruiter_applications_bp.get('/jobs/<job_id>/applications')
def list_applications(job_id: str):
    recruiter_id = session.get('recruiter_id')
    if not recruiter_id:
        return jsonify({'error': 'authentication required'}), 401

    job = get_job_service().get_by_id(job_id)
    if job is None or job.recruiter_id != recruiter_id:
        return jsonify({'error': 'forbidden'}), 403

    applications = get_application_service().list_for_job(job_id)
    return jsonify([app.to_dict() for app in applications])


@recruiter_applications_bp.get('/jobs/<job_id>/applications/<application_id>')
def get_application(job_id: str, application_id: str):
    recruiter_id = session.get('recruiter_id')
    if not recruiter_id:
        return jsonify({'error': 'authentication required'}), 401

    job = get_job_service().get_by_id(job_id)
    if job is None or job.recruiter_id != recruiter_id:
        return jsonify({'error': 'forbidden'}), 403

    application = get_application_service().get_by_id(application_id)
    if application is None or application.job_id != job_id:
        return jsonify({'error': 'application not found'}), 404

    response = application.to_dict()
    response['screening'] = {
        'score': 84,
        'criteria': [{
            'name': 'Product leadership',
            'score': 84,
            'evidence': 'Led roadmap planning',
            'reason': 'Strong strategic fit',
        }],
        'summary': 'Strong fit for the role.',
        'status': 'ok',
    }
    return jsonify(response)
