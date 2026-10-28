from __future__ import annotations

from typing import BinaryIO

from flask import current_app

from ..jobs.models import Job
from ..storage.base import StorageError
from ..storage.minio import MinioStorage
from .models import Application, StoredCv


class ApplicationService:
    def __init__(self, storage=None) -> None:
        self._storage = storage or MinioStorage()
        self._applications_by_id: dict[str, Application] = {}
        self._applications_by_job: dict[str, list[Application]] = {}

    def submit_application(self, job: Job, applicant_name: str, email: str, cv_file: BinaryIO, content_type: str) -> Application:
        if job is None or job.status != 'published':
            raise ValueError('job not found')

        trimmed_name = applicant_name.strip()
        trimmed_email = email.strip().lower()
        if not trimmed_name or not trimmed_email:
            raise ValueError('name and email are required')

        try:
            stored_cv = self._storage.save(cv_file, content_type)
        except StorageError:
            raise

        application = Application.create(job.id, trimmed_name, trimmed_email, StoredCv(**stored_cv.to_dict()))
        self._applications_by_id[application.id] = application
        self._applications_by_job.setdefault(job.id, []).append(application)
        return application

    def get_by_id(self, application_id: str) -> Application | None:
        return self._applications_by_id.get(application_id)

    def list_for_job(self, job_id: str) -> list[Application]:
        return list(self._applications_by_job.get(job_id, []))


def get_application_service() -> ApplicationService:
    service = current_app.extensions.get('application_service')
    if service is None:
        service = ApplicationService()
        current_app.extensions['application_service'] = service
    return service
