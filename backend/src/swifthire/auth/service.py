from __future__ import annotations

from typing import Dict

from flask import current_app

from .models import Recruiter


class RecruiterService:
    def __init__(self) -> None:
        self._users_by_email: Dict[str, Recruiter] = {}
        self._users_by_id: Dict[str, Recruiter] = {}

    def create_recruiter(self, name: str, email: str, password: str) -> Recruiter:
        normalized_email = email.strip().lower()
        if normalized_email in self._users_by_email:
            raise ValueError('email already registered')

        recruiter = Recruiter.create(name=name, email=normalized_email, password=password)
        self._users_by_email[normalized_email] = recruiter
        self._users_by_id[recruiter.id] = recruiter
        return recruiter

    def authenticate(self, email: str, password: str) -> Recruiter | None:
        recruiter = self._users_by_email.get(email.strip().lower())
        if recruiter is None or not recruiter.verify_password(password):
            return None
        return recruiter

    def get_by_id(self, recruiter_id: str) -> Recruiter | None:
        return self._users_by_id.get(recruiter_id)


def get_recruiter_service() -> RecruiterService:
    service = current_app.extensions.get('recruiter_service')
    if service is None:
        service = RecruiterService()
        current_app.extensions['recruiter_service'] = service
    return service
