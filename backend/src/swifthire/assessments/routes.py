from __future__ import annotations

from flask import Blueprint, jsonify, request, session

from ..applications.service import get_application_service
from ..jobs.service import get_job_service
from ..notifications.base import EmailSender, SendResult
from ..notifications.resend import ResendEmailSender
from .service import get_assessment_service

assessments_bp = Blueprint('assessments', __name__, url_prefix='/api')


@assessments_bp.get('/assessments/<token>')
def get_assessment(token: str):
    service = get_assessment_service()
    assessment = service.get_by_token(token)
    if assessment is None or assessment.used_token:
        return jsonify({'error': 'assessment not found'}), 404
    if assessment.status == 'not_sent':
        return jsonify({'error': 'assessment not available'}), 403
    if assessment.status == 'pending_review':
        return jsonify({'status': 'pending_review', 'questions': [question.to_dict(include_answer=False) for question in assessment.questions]}), 200
    return jsonify({'error': 'assessment not found'}), 404


@assessments_bp.post('/assessments/<token>/submit')
def submit_assessment(token: str):
    service = get_assessment_service()
    assessment = service.get_by_token(token)
    if assessment is None or assessment.used_token:
        return jsonify({'error': 'assessment not found'}), 404

    data = request.get_json(silent=True) or {}
    answers = data.get('answers') or {}
    try:
        updated = service.submit_answers(token, answers)
    except LookupError:
        return jsonify({'error': 'assessment not found'}), 404
    return jsonify({'status': 'submitted', 'score': updated.score})


@assessments_bp.post('/recruiter/jobs/<job_id>/applications/<application_id>/invite')
def invite_application(job_id: str, application_id: str):
    recruiter_id = session.get('recruiter_id')
    if not recruiter_id:
        return jsonify({'error': 'authentication required'}), 401

    job = get_job_service().get_by_id(job_id)
    if job is None or job.recruiter_id != recruiter_id:
        return jsonify({'error': 'forbidden'}), 403

    application = get_application_service().get_by_id(application_id)
    if application is None or application.job_id != job_id:
        return jsonify({'error': 'application not found'}), 404

    payload = request.get_json(silent=True) or {}
    stage = payload.get('stage', 'online_assessment')
    deliver = payload.get('deliver', True)
    service = get_assessment_service()
    assessment = service.create_assessment(application_id, job_id, stage)

    if deliver:
        sender: EmailSender = ResendEmailSender()
        result = sender.send(application.email, f'Your {stage} assessment', f'Use token: {assessment.token}', assessment.token)
        status = 'sent' if result.status == 'sent' else 'failed'
        if status == 'sent':
            assessment.status = 'pending_review'
            assessment.sent_at = result.message_id or assessment.sent_at
        else:
            assessment.status = 'not_sent'
            assessment.sent_at = ''
    else:
        status = 'not_sent'
        assessment.status = 'not_sent'
        assessment.sent_at = ''

    response = {
        'id': assessment.id,
        'application_id': application_id,
        'job_id': job_id,
        'stage': stage,
        'token': assessment.token,
        'status': status,
    }
    return jsonify(response), 201


@assessments_bp.get('/recruiter/jobs/<job_id>/applications/<application_id>/assessments')
def list_application_assessments(job_id: str, application_id: str):
    recruiter_id = session.get('recruiter_id')
    if not recruiter_id:
        return jsonify({'error': 'authentication required'}), 401

    job = get_job_service().get_by_id(job_id)
    if job is None or job.recruiter_id != recruiter_id:
        return jsonify({'error': 'forbidden'}), 403

    application = get_application_service().get_by_id(application_id)
    if application is None or application.job_id != job_id:
        return jsonify({'error': 'application not found'}), 404

    assessments = get_assessment_service().get_application_assessments(application_id)
    return jsonify([{
        'id': item.id,
        'application_id': item.application_id,
        'job_id': item.job_id,
        'stage': item.stage,
        'status': item.status,
        'token': item.token,
    } for item in assessments])
