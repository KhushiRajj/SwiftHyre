from __future__ import annotations

from flask import Blueprint, jsonify, request, session

from ..applications.service import get_application_service
from ..jobs.service import get_job_service
from .service import TransitionConflict, get_workflow_service

workflow_bp = Blueprint('workflow', __name__, url_prefix='/api/recruiter')


def _decision_context(application_id: str, job_id: str | None = None):
    recruiter_id = session.get('recruiter_id')
    if not recruiter_id:
        return None, None, None, (jsonify({'error': 'authentication required'}), 401)

    application = get_application_service().get_by_id(application_id)
    if application is None:
        return None, None, None, (jsonify({'error': 'application not found'}), 404)

    if job_id is None:
        job_id = application.job_id

    job = get_job_service().get_by_id(job_id)
    if job is None or job.recruiter_id != recruiter_id:
        return None, None, None, (jsonify({'error': 'forbidden'}), 403)

    if application.job_id != job_id:
        return None, None, None, (jsonify({'error': 'application not found'}), 404)

    return recruiter_id, job, application, None


@workflow_bp.post('/jobs/<job_id>/applications/<application_id>/decisions')
def create_decision(job_id: str, application_id: str):
    recruiter_id, job, application, error = _decision_context(application_id, job_id)
    if error is not None:
        return error

    data = request.get_json(silent=True) or {}
    decision = data.get('decision')
    expected_stage = data.get('expected_stage')
    idempotency_key = data.get('idempotency_key')
    recommendation_score = data.get('recommendation_score')

    if decision is None or expected_stage is None:
        return jsonify({'error': 'decision and expected_stage are required'}), 400

    service = get_workflow_service()
    existing = service.get_existing_decision(job_id, application_id, idempotency_key)
    if existing is not None:
        return jsonify(existing.to_dict()), 200

    try:
        record = service.decide(
            job_id=job_id,
            application_id=application_id,
            recruiter_id=recruiter_id,
            decision=decision,
            expected_stage=expected_stage,
            idempotency_key=idempotency_key,
            recommendation_score=recommendation_score,
        )
    except LookupError as exc:
        return jsonify({'error': str(exc)}), 404
    except PermissionError:
        return jsonify({'error': 'forbidden'}), 403
    except TransitionConflict:
        return jsonify({'error': 'invalid transition'}), 409
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    response = jsonify(record.to_dict())
    response.status_code = 201
    return response


@workflow_bp.post('/applications/<application_id>/decisions')
def create_decision_alias(application_id: str):
    recruiter_id, job, application, error = _decision_context(application_id)
    if error is not None:
        return error

    data = request.get_json(silent=True) or {}
    decision = data.get('decision')
    expected_stage = data.get('expected_stage')
    idempotency_key = data.get('idempotency_key')
    recommendation_score = data.get('recommendation_score')
    job_id = application.job_id

    if decision is None or expected_stage is None:
        return jsonify({'error': 'decision and expected_stage are required'}), 400

    service = get_workflow_service()
    existing = service.get_existing_decision(job_id, application_id, idempotency_key)
    if existing is not None:
        return jsonify(existing.to_dict()), 200

    try:
        record = service.decide(
            job_id=job_id,
            application_id=application_id,
            recruiter_id=recruiter_id,
            decision=decision,
            expected_stage=expected_stage,
            idempotency_key=idempotency_key,
            recommendation_score=recommendation_score,
        )
    except LookupError as exc:
        return jsonify({'error': str(exc)}), 404
    except PermissionError:
        return jsonify({'error': 'forbidden'}), 403
    except TransitionConflict:
        return jsonify({'error': 'invalid transition'}), 409
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    response = jsonify(record.to_dict())
    response.status_code = 201
    return response
