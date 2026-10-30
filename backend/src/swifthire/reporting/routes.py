from __future__ import annotations

from flask import Blueprint, jsonify, session

from .service import get_reporting_service

reporting_bp = Blueprint('reporting', __name__, url_prefix='/api/recruiter')


@reporting_bp.get('/jobs/<job_id>/dashboard')
def get_job_dashboard(job_id: str):
    recruiter_id = session.get('recruiter_id')
    if not recruiter_id:
        return jsonify({'error': 'authentication required'}), 401

    dashboard = get_reporting_service().get_job_dashboard(job_id, recruiter_id)
    if dashboard is None:
        return jsonify({'error': 'job not found'}), 404
    return jsonify(dashboard)
