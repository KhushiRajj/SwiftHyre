from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4


@dataclass
class Job:
    id: str
    recruiter_id: str
    title: str
    description: str
    status: str
    public_slug: str

    @classmethod
    def create(cls, recruiter_id: str, title: str, description: str, status: str, public_slug: str) -> 'Job':
        return cls(
            id=str(uuid4()),
            recruiter_id=recruiter_id,
            title=title.strip(),
            description=description.strip(),
            status=status,
            public_slug=public_slug,
        )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'recruiter_id': self.recruiter_id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'public_slug': self.public_slug,
        }
