from __future__ import annotations

from flask import Blueprint, jsonify, request, session

from ..applications.service import get_application_service
from ..assessments.service import get_assessment_service
from ..jobs.service import get_job_service
from .service import MAX_SOURCE_BYTES, SubmissionInProgress, get_coding_service

coding_bp = Blueprint('coding', __name__, url_prefix='/api')


def _require_recruiter_id() -> str | None:
    recruiter_id = session.get('recruiter_id')
    return recruiter_id if recruiter_id else None


@coding_bp.post('/recruiter/jobs/<job_id>/coding-challenges')
def create_challenge(job_id: str):
    recruiter_id = _require_recruiter_id()
    if recruiter_id is None:
        return jsonify({'error': 'authentication required'}), 401

    job = get_job_service().get_by_id(job_id)
    if job is None or job.recruiter_id != recruiter_id:
        return jsonify({'error': 'forbidden'}), 403

    payload = request.get_json(silent=True) or {}
    title = str(payload.get('title', '')).strip()
    prompt = str(payload.get('prompt', '')).strip()
    allowed_languages = payload.get('allowed_languages') or []
    public_test_cases = payload.get('public_test_cases') or []
    private_test_cases = payload.get('private_test_cases') or []

    if (
        not title
        or not prompt
        or not isinstance(allowed_languages, list)
        or not allowed_languages
        or any(not isinstance(language, str) or not language.strip() for language in allowed_languages)
        or not isinstance(public_test_cases, list)
        or not isinstance(private_test_cases, list)
        or not private_test_cases
    ):
        return jsonify({'error': 'title, prompt, allowed languages and at least one private test case are required'}), 400

    try:
        challenge = get_coding_service().create_challenge(
            job_id=job_id,
            recruiter_id=recruiter_id,
            title=title,
            prompt=prompt,
            allowed_languages=allowed_languages,
            public_test_cases=public_test_cases,
            private_test_cases=private_test_cases,
        )
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    response = jsonify(challenge.to_dict(include_private=True))
    response.status_code = 201
    return response


@coding_bp.get('/public/jobs/<slug>/coding-challenges')
def list_public_challenges(slug: str):
    job = get_job_service().get_by_slug(slug)
    if job is None or job.status != 'published':
        return jsonify({'error': 'job not found'}), 404

    challenges = get_coding_service().list_for_job(job.id)
    return jsonify([challenge.to_public_dict() for challenge in challenges])


@coding_bp.post('/public/coding-challenges/<challenge_id>/submissions')
def submit_challenge(challenge_id: str):
    service = get_coding_service()
    challenge = service.get_by_id(challenge_id)
    if challenge is None:
        return jsonify({'error': 'challenge not found'}), 404

    payload = request.get_json(silent=True) or {}
    language = str(payload.get('language', '')).strip().lower()
    source = payload.get('source', '')

    if not isinstance(source, str):
        return jsonify({'error': 'source is required'}), 400
    if '\x00' in source:
        return jsonify({'error': 'source cannot contain NUL characters'}), 400
    try:
        source_bytes = source.encode('utf-8')
    except UnicodeEncodeError:
        return jsonify({'error': 'source must be valid UTF-8'}), 400
    if len(source_bytes) > MAX_SOURCE_BYTES:
        return jsonify({'error': 'source is too large'}), 400
    if language not in challenge.allowed_languages:
        return jsonify({'error': 'language is not allowed for this challenge'}), 400

    assessment_token = payload.get('assessment_token')
    if not isinstance(assessment_token, str) or not assessment_token:
        return jsonify({'error': 'active coding assessment token required'}), 401

    assessment = get_assessment_service().get_by_token(assessment_token)
    if assessment is None:
        return jsonify({'error': 'assessment not found'}), 404

    application = get_application_service().get_by_id(assessment.application_id)
    if (
        assessment.stage != 'coding_assessment'
        or assessment.job_id != challenge.job_id
        or application is None
        or application.job_id != challenge.job_id
        or application.status == 'rejected'
        or application.current_stage != assessment.stage
    ):
        return jsonify({'error': 'assessment is not valid for the current application stage'}), 403

    existing = service.get_submission_for_application(challenge_id, application.id)
    if assessment.used_token:
        if (
            existing is not None
            and existing.language == language
            and existing.source == source
            and existing.status in {'completed', 'partial'}
        ):
            return jsonify(existing.to_dict()), 200
        return jsonify({'error': 'assessment token has already been used'}), 409
    if assessment.status != 'pending_review':
        return jsonify({'error': 'coding assessment is not available'}), 403

    try:
        submission = service.create_submission(challenge_id, application.id, language, source)
    except SubmissionInProgress as exc:
        return jsonify({'error': str(exc)}), 409
    except (LookupError, ValueError) as exc:
        message = str(exc)
        status = 404 if isinstance(exc, LookupError) else 400
        return jsonify({'error': message}), status

    if submission.status in {'completed', 'partial'}:
        assessment.used_token = True
        assessment.status = 'submitted'
        assessment.score = submission.score_percentage

    response = jsonify(submission.to_dict())
    response.status_code = 201 if existing is None else 200
    return response


@coding_bp.get('/recruiter/jobs/<job_id>/coding-challenges/<challenge_id>/submissions')
def list_challenge_submissions(job_id: str, challenge_id: str):
    recruiter_id = _require_recruiter_id()
    if recruiter_id is None:
        return jsonify({'error': 'authentication required'}), 401

    job = get_job_service().get_by_id(job_id)
    if job is None or job.recruiter_id != recruiter_id:
        return jsonify({'error': 'forbidden'}), 403

    service = get_coding_service()
    challenge = service.get_by_id(challenge_id)
    if challenge is None or challenge.job_id != job_id:
        return jsonify({'error': 'challenge not found'}), 404

    applications = {
        application.id: application
        for application in get_application_service().list_for_job(job_id)
    }
    results = []
    for submission in service.list_submissions(challenge_id):
        application = applications.get(submission.application_id)
        if application is not None:
            results.append(submission.to_recruiter_dict(application.applicant_name))
    return jsonify(results)
