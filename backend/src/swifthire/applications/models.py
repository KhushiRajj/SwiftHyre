from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class StoredCv:
    object_key: str
    content_type: str
    size_bytes: int

    def to_dict(self) -> dict:
        return {
            'object_key': self.object_key,
            'content_type': self.content_type,
            'size_bytes': self.size_bytes,
        }


@dataclass
class Application:
    id: str
    job_id: str
    applicant_name: str
    email: str
    cv: StoredCv
    status: str
    created_at: str

    @classmethod
    def create(cls, job_id: str, applicant_name: str, email: str, cv: StoredCv) -> 'Application':
        return cls(
            id=str(uuid4()),
            job_id=job_id,
            applicant_name=applicant_name.strip(),
            email=email.strip().lower(),
            cv=cv,
            status='pending',
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'job_id': self.job_id,
            'applicant_name': self.applicant_name,
            'email': self.email,
            'cv': self.cv.to_dict(),
            'status': self.status,
            'created_at': self.created_at,
        }
