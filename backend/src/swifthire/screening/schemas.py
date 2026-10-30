from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class CriterionResult:
    name: str
    score: int
    evidence: str
    reason: str

    def __post_init__(self) -> None:
        if not 0 <= self.score <= 100:
            raise ValueError('criterion score must be between 0 and 100')
        if not self.name.strip() or not self.evidence.strip() or not self.reason.strip():
            raise ValueError('criterion result fields are required')


@dataclass
class MatchResult:
    score: int | None
    criteria: list[CriterionResult] = field(default_factory=list)
    summary: str = ''
    status: str = 'ok'

    def __post_init__(self) -> None:
        if self.score is not None and not 0 <= self.score <= 100:
            raise ValueError('score must be between 0 and 100')
        if not self.summary.strip():
            raise ValueError('summary is required')
        if self.score is None and self.status != 'screening_failed':
            self.status = 'screening_failed'


@dataclass
class ScreeningFailure:
    status: Literal['screening_failed'] = 'screening_failed'
    score: None = None
    criteria: list[CriterionResult] = field(default_factory=list)
    summary: str = 'Screening failed; please retry or ask for review.'
