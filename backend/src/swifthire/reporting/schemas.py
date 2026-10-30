from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

ResultState = Literal['pending', 'completed', 'failed', 'unavailable', 'not_configured']


@dataclass
class StageResult:
    stage_key: str
    state: ResultState
    score: int | None = None
    criteria: list[dict[str, Any]] = field(default_factory=list)
    summary: str | None = None


@dataclass
class MatchResult:
    state: ResultState
    score: int | None = None
    criteria: list[dict[str, Any]] = field(default_factory=list)
    summary: str | None = None
