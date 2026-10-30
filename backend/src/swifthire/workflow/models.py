from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class ApplicationDecision:
    id: str
    application_id: str
    job_id: str
    recruiter_id: str
    decision: str
    expected_stage: str
    status: str
    recommendation_score: int | None = None
    idempotency_key: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def create(
        cls,
        application_id: str,
        job_id: str,
        recruiter_id: str,
        decision: str,
        expected_stage: str,
        status: str,
        recommendation_score: int | None = None,
        idempotency_key: str | None = None,
    ) -> 'ApplicationDecision':
        return cls(
            id=str(uuid4()),
            application_id=application_id,
            job_id=job_id,
            recruiter_id=recruiter_id,
            decision=decision,
            expected_stage=expected_stage,
            status=status,
            recommendation_score=recommendation_score,
            idempotency_key=idempotency_key,
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            'id': self.id,
            'application_id': self.application_id,
            'job_id': self.job_id,
            'recruiter_id': self.recruiter_id,
            'decision': self.decision,
            'expected_stage': self.expected_stage,
            'status': self.status,
            'created_at': self.created_at,
        }
        if self.recommendation_score is not None:
            payload['recommendation_score'] = self.recommendation_score
        if self.idempotency_key is not None:
            payload['idempotency_key'] = self.idempotency_key
        return payload
