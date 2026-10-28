from __future__ import annotations

import re
from typing import Dict, List

from flask import current_app

from .models import Job

VALID_STATUSES = {'draft', 'published', 'closed'}


class JobService:
    def __init__(self) -> None:
        self._jobs_by_id: Dict[str, Job] = {}
        self._jobs_by_slug: Dict[str, Job] = {}

    def create_job(self, recruiter_id: str, title: str, description: str, status: str = 'draft', public_slug: str | None = None) -> Job:
        slug = public_slug or self._generate_slug(title)
        while slug in self._jobs_by_slug:
            slug = f"{slug}-{len(self._jobs_by_slug)}"

        job = Job.create(
            recruiter_id=recruiter_id,
            title=title,
            description=description,
            status=status if status in VALID_STATUSES else 'draft',
            public_slug=slug,
        )
        self._jobs_by_id[job.id] = job
        self._jobs_by_slug[job.public_slug] = job
        return job

    def list_for_recruiter(self, recruiter_id: str) -> List[Job]:
        return [job for job in self._jobs_by_id.values() if job.recruiter_id == recruiter_id]

    def get_by_id(self, job_id: str) -> Job | None:
        return self._jobs_by_id.get(job_id)

    def get_by_slug(self, slug: str) -> Job | None:
        return self._jobs_by_slug.get(slug)

    def update_job(self, job_id: str, recruiter_id: str, **updates) -> Job:
        job = self.get_by_id(job_id)
        if job is None or job.recruiter_id != recruiter_id:
            raise ValueError('job not found or not owned by recruiter')

        if 'title' in updates:
            job.title = updates['title'].strip()
        if 'description' in updates:
            job.description = updates['description'].strip()
        if 'status' in updates:
            job.status = updates['status'] if updates['status'] in VALID_STATUSES else 'draft'
        if 'public_slug' in updates:
            new_slug = updates['public_slug'].strip()
            if new_slug:
                self._jobs_by_slug.pop(job.public_slug, None)
                job.public_slug = new_slug
                self._jobs_by_slug[job.public_slug] = job

        return job

    def _generate_slug(self, title: str) -> str:
        base = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
        if not base:
            base = 'job'
        return base


def get_job_service() -> JobService:
    service = current_app.extensions.get('job_service')
    if service is None:
        service = JobService()
        current_app.extensions['job_service'] = service
    return service
