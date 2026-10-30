from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

DEFAULT_STAGE_ORDER = ['online_assessment', 'coding_assessment', 'voice_interview']


@dataclass
class Job:
    id: str
    recruiter_id: str
    title: str
    description: str
    status: str
    public_slug: str
    stage_order: list[str] = field(default_factory=lambda: DEFAULT_STAGE_ORDER.copy())
    recommendation_threshold: int = 80

    @classmethod
    def create(
        cls,
        recruiter_id: str,
        title: str,
        description: str,
        status: str,
        public_slug: str,
        stage_order: list[str] | None = None,
        recommendation_threshold: int | None = None,
    ) -> 'Job':
        ordered_stages = list(stage_order or DEFAULT_STAGE_ORDER)
        normalized_threshold = 80
        if recommendation_threshold is not None:
            try:
                normalized_threshold = int(recommendation_threshold)
            except (TypeError, ValueError):
                normalized_threshold = 80
        if not 0 <= normalized_threshold <= 100:
            normalized_threshold = 80

        return cls(
            id=str(uuid4()),
            recruiter_id=recruiter_id,
            title=title.strip(),
            description=description.strip(),
            status=status,
            public_slug=public_slug,
            stage_order=ordered_stages,
            recommendation_threshold=normalized_threshold,
        )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'recruiter_id': self.recruiter_id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'public_slug': self.public_slug,
            'stage_order': list(self.stage_order),
            'recommendation_threshold': self.recommendation_threshold,
        }
