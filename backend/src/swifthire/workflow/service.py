from __future__ import annotations

from typing import Any

from flask import current_app

from ..applications.service import get_application_service
from ..jobs.service import get_job_service
from .models import ApplicationDecision

VALID_DECISIONS = {'advance', 'reject'}
DEFAULT_STAGE_ORDER = ['online_assessment', 'coding_assessment', 'voice_interview']


class TransitionConflict(ValueError):
    pass


class WorkflowService:
    def __init__(self) -> None:
        self._decisions_by_id: dict[str, ApplicationDecision] = {}
        self._decision_keys_by_application: dict[str, dict[str, ApplicationDecision]] = {}

    def list_decisions_for_application(self, application_id: str) -> list[ApplicationDecision]:
        decisions = [
            decision
            for decision in self._decisions_by_id.values()
            if decision.application_id == application_id
        ]
        return sorted(decisions, key=lambda decision: (decision.created_at, decision.id))

    def get_existing_decision(self, job_id: str, application_id: str, idempotency_key: str | None) -> ApplicationDecision | None:
        if not idempotency_key:
            return None
        return self._decision_keys_by_application.get(f'{job_id}:{application_id}', {}).get(idempotency_key)

    def decide(
        self,
        job_id: str,
        application_id: str,
        recruiter_id: str,
        decision: str,
        expected_stage: str,
        idempotency_key: str | None = None,
        recommendation_score: int | None = None,
    ) -> ApplicationDecision:
        job = get_job_service().get_by_id(job_id)
        if job is None:
            raise LookupError('job not found')
        if job.recruiter_id != recruiter_id:
            raise PermissionError('forbidden')

        application = get_application_service().get_by_id(application_id)
        if application is None or application.job_id != job_id:
            raise LookupError('application not found')

        normalized = (decision or '').strip().lower()
        if normalized not in VALID_DECISIONS:
            raise ValueError('decision must be advance or reject')

        if expected_stage not in job.stage_order:
            raise TransitionConflict('invalid stage transition')

        if idempotency_key:
            key_map = self._decision_keys_by_application.setdefault(f'{job_id}:{application_id}', {})
            existing = key_map.get(idempotency_key)
            if existing is not None:
                return existing

        current_stage = getattr(application, 'current_stage', job.stage_order[0])
        if current_stage != expected_stage:
            raise TransitionConflict('expected stage does not match current stage')

        threshold = int(job.recommendation_threshold)
        status = 'decision'
        if recommendation_score is not None and recommendation_score < threshold:
            status = 'recommendation'

        decision_obj = ApplicationDecision.create(
            application_id=application_id,
            job_id=job_id,
            recruiter_id=recruiter_id,
            decision=normalized,
            expected_stage=expected_stage,
            status=status,
            recommendation_score=recommendation_score,
            idempotency_key=idempotency_key,
        )

        self._decisions_by_id[decision_obj.id] = decision_obj
        if idempotency_key:
            self._decision_keys_by_application[f'{job_id}:{application_id}'][idempotency_key] = decision_obj

        if normalized == 'reject':
            application.status = 'rejected'
        else:
            current_stage_index = job.stage_order.index(expected_stage)
            if current_stage_index + 1 < len(job.stage_order):
                application.current_stage = job.stage_order[current_stage_index + 1]

        return decision_obj


def get_workflow_service() -> WorkflowService:
    service = current_app.extensions.get('workflow_service')
    if service is None:
        service = WorkflowService()
        current_app.extensions['workflow_service'] = service
    return service
