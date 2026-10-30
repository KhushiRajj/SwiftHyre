from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from werkzeug.security import check_password_hash, generate_password_hash


@dataclass
class Recruiter:
    id: str
    name: str
    email: str
    password_hash: str

    @classmethod
    def create(cls, name: str, email: str, password: str) -> 'Recruiter':
        return cls(
            id=str(uuid4()),
            name=name.strip(),
            email=email.strip().lower(),
            password_hash=generate_password_hash(password),
        )

    def verify_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_public_dict(self) -> dict[str, str]:
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
        }
