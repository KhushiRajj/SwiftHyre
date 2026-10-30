from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class CodingTestCase:
    input: str
    expected_output: str

    def to_dict(self) -> dict[str, str]:
        return {
            'input': self.input,
            'expected_output': self.expected_output,
        }


@dataclass
class CodingChallenge:
    id: str
    job_id: str
    recruiter_id: str
    title: str
    prompt: str
    allowed_languages: list[str]
    public_test_cases: list[CodingTestCase] = field(default_factory=list)
    private_test_cases: list[CodingTestCase] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def create(
        cls,
        job_id: str,
        recruiter_id: str,
        title: str,
        prompt: str,
        allowed_languages: list[str],
        public_test_cases: list[CodingTestCase] | None = None,
        private_test_cases: list[CodingTestCase] | None = None,
    ) -> 'CodingChallenge':
        return cls(
            id=str(uuid4()),
            job_id=job_id,
            recruiter_id=recruiter_id,
            title=title.strip(),
            prompt=prompt.strip(),
            allowed_languages=[str(item).strip().lower() for item in (allowed_languages or []) if str(item).strip()],
            public_test_cases=list(public_test_cases or []),
            private_test_cases=list(private_test_cases or []),
        )

    def to_public_dict(self) -> dict:
        return {
            'id': self.id,
            'job_id': self.job_id,
            'title': self.title,
            'prompt': self.prompt,
            'allowed_languages': list(self.allowed_languages),
            'public_test_cases': [case.to_dict() for case in self.public_test_cases],
            'created_at': self.created_at,
        }

    def to_dict(self, include_private: bool = True) -> dict:
        payload = self.to_public_dict()
        if include_private:
            payload['private_test_cases'] = [case.to_dict() for case in self.private_test_cases]
        return payload


@dataclass
class CodingSubmission:
    id: str
    challenge_id: str
    application_id: str
    language: str
    source: str
    status: str = 'unavailable'
    score_percentage: int | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def create(
        cls,
        challenge_id: str,
        application_id: str,
        language: str,
        source: str,
        status: str,
        score_percentage: int | None = None,
    ) -> 'CodingSubmission':
        return cls(
            id=str(uuid4()),
            challenge_id=challenge_id,
            application_id=application_id,
            language=language.strip().lower(),
            source=source,
            status=status,
            score_percentage=score_percentage,
        )

    def to_dict(self) -> dict:
        payload = {
            'id': self.id,
            'challenge_id': self.challenge_id,
            'language': self.language,
            'status': self.status,
            'created_at': self.created_at,
        }
        if self.score_percentage is not None:
            payload['score'] = self.score_percentage
        if self.status == 'processing':
            payload['message'] = 'Submission is still processing. Retry this submission for the result.'
        elif self.status in {'unavailable', 'timeout'}:
            payload['message'] = 'The code execution provider did not complete this submission. Retry after the provider is available.'
        return payload

    def to_recruiter_dict(self, candidate_name: str) -> dict:
        return {
            'id': self.id,
            'candidate_name': candidate_name,
            'language': self.language,
            'status': self.status,
            'score': self.score_percentage,
            'created_at': self.created_at,
        }
