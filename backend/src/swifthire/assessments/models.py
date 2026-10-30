from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from secrets import token_urlsafe
from typing import Any


@dataclass
class AssessmentQuestion:
    id: str
    prompt: str
    choices: list[str]
    answer: str | None = None

    def to_dict(self, include_answer: bool = True) -> dict[str, Any]:
        payload = {
            'id': self.id,
            'prompt': self.prompt,
            'choices': list(self.choices),
        }
        if include_answer:
            payload['answer'] = self.answer
        return payload


@dataclass
class Assessment:
    id: str
    application_id: str
    job_id: str
    stage: str
    token: str
    questions: list[AssessmentQuestion] = field(default_factory=list)
    status: str = 'pending_review'
    sent_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    used_token: bool = False
    score: int | None = None
    answers: dict[str, str] = field(default_factory=dict)

    @classmethod
    def create(cls, application_id: str, job_id: str, stage: str) -> 'Assessment':
        return cls(
            id=f'assessment-{token_urlsafe(8)}',
            application_id=application_id,
            job_id=job_id,
            stage=stage,
            token=token_urlsafe(16),
            questions=[],
            status='pending_review',
        )

    def to_dict(self, include_answers: bool = True) -> dict[str, Any]:
        return {
            'id': self.id,
            'application_id': self.application_id,
            'job_id': self.job_id,
            'stage': self.stage,
            'token': self.token,
            'status': self.status,
            'sent_at': self.sent_at,
            'used_token': self.used_token,
            'score': self.score,
            'questions': [question.to_dict(include_answer=include_answers) for question in self.questions],
            'answers': dict(self.answers),
        }
