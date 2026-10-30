from __future__ import annotations

from threading import Lock

from flask import current_app

from .models import CodingChallenge, CodingSubmission, CodingTestCase
from .runner import MAX_CODE_BYTES, CodeRunner, RunnerProvider
from .scoring import ChallengeScorer

MAX_SOURCE_BYTES = MAX_CODE_BYTES
MAX_PRIVATE_TEST_CASES = 8
MAX_TEST_INPUT_BYTES = MAX_CODE_BYTES
MAX_TEST_OUTPUT_BYTES = 65536


class SubmissionInProgress(ValueError):
    pass


class CodingChallengeService:
    def __init__(self, runner: RunnerProvider | None = None) -> None:
        self._challenges_by_id: dict[str, CodingChallenge] = {}
        self._challenges_by_job: dict[str, list[CodingChallenge]] = {}
        self._submissions_by_challenge: dict[str, list[CodingSubmission]] = {}
        self._submissions_by_candidate: dict[str, CodingSubmission] = {}
        self._submission_lock = Lock()
        self._runner = runner or CodeRunner()
        self._scorer = ChallengeScorer(self._runner)

    def create_challenge(
        self,
        job_id: str,
        recruiter_id: str,
        title: str,
        prompt: str,
        allowed_languages: list[str],
        public_test_cases: list[dict] | None = None,
        private_test_cases: list[dict] | None = None,
    ) -> CodingChallenge:
        normalized_languages = []
        for language in allowed_languages or []:
            normalized = str(language).strip().lower()
            if normalized:
                normalized_languages.append(normalized)

        if not title.strip() or not prompt.strip():
            raise ValueError('title and prompt are required')
        if not normalized_languages:
            raise ValueError('allowed languages are required')
        if not private_test_cases:
            raise ValueError('at least one private test case is required')
        if len(private_test_cases) > MAX_PRIVATE_TEST_CASES:
            raise ValueError('at most 8 private test cases are allowed')

        public_cases = self._normalize_test_cases(public_test_cases or [])
        private_cases = self._normalize_test_cases(private_test_cases)

        challenge = CodingChallenge.create(
            job_id=job_id,
            recruiter_id=recruiter_id,
            title=title,
            prompt=prompt,
            allowed_languages=normalized_languages,
            public_test_cases=public_cases,
            private_test_cases=private_cases,
        )
        self._challenges_by_id[challenge.id] = challenge
        self._challenges_by_job.setdefault(job_id, []).append(challenge)
        return challenge

    def list_for_job(self, job_id: str) -> list[CodingChallenge]:
        return list(self._challenges_by_job.get(job_id, []))

    def get_by_id(self, challenge_id: str) -> CodingChallenge | None:
        return self._challenges_by_id.get(challenge_id)

    def get_submission_for_application(self, challenge_id: str, application_id: str) -> CodingSubmission | None:
        with self._submission_lock:
            return self._submissions_by_candidate.get(f'{challenge_id}:{application_id}')

    def list_submissions(self, challenge_id: str) -> list[CodingSubmission]:
        with self._submission_lock:
            return list(self._submissions_by_challenge.get(challenge_id, []))

    def create_submission(
        self,
        challenge_id: str,
        application_id: str,
        language: str,
        source: str,
    ) -> CodingSubmission:
        challenge = self.get_by_id(challenge_id)
        if challenge is None:
            raise LookupError('challenge not found')

        normalized_language = (language or '').strip().lower()
        if normalized_language not in challenge.allowed_languages:
            raise ValueError('language is not allowed for this challenge')

        if not isinstance(source, str):
            raise ValueError('source is required')
        if '\x00' in source:
            raise ValueError('source cannot contain NUL characters')
        try:
            source_size = len(source.encode('utf-8'))
        except UnicodeEncodeError as exc:
            raise ValueError('source must be valid UTF-8') from exc
        if source_size > MAX_SOURCE_BYTES:
            raise ValueError('source is too large')

        candidate_key = f'{challenge_id}:{application_id}'
        with self._submission_lock:
            existing = self._submissions_by_candidate.get(candidate_key)
            if existing is not None and existing.status in {'completed', 'partial'}:
                if existing.language != normalized_language or existing.source != source:
                    raise ValueError('a completed submission already exists for this stage')
                return existing
            if existing is not None and existing.status == 'processing':
                if existing.language != normalized_language or existing.source != source:
                    raise SubmissionInProgress('another submission is already in progress')
                return existing

            created = existing is None
            if created:
                submission = CodingSubmission.create(
                    challenge_id,
                    application_id,
                    normalized_language,
                    source,
                    status='processing',
                )
                self._submissions_by_challenge.setdefault(challenge_id, []).append(submission)
                self._submissions_by_candidate[candidate_key] = submission
                previous = None
            else:
                submission = existing
                previous = (submission.language, submission.source, submission.status, submission.score_percentage)
                submission.language = normalized_language
                submission.source = source
                submission.status = 'processing'
                submission.score_percentage = None

        completed = False
        try:
            scoring = self._scorer.score(challenge, source, normalized_language)
            with self._submission_lock:
                submission.status = scoring['status']
                submission.score_percentage = scoring['score_percentage']
            completed = True
            return submission
        finally:
            if not completed:
                with self._submission_lock:
                    if created:
                        self._submissions_by_candidate.pop(candidate_key, None)
                        submissions = self._submissions_by_challenge[challenge_id]
                        submissions.remove(submission)
                        if not submissions:
                            self._submissions_by_challenge.pop(challenge_id)
                    elif previous is not None:
                        submission.language, submission.source, submission.status, submission.score_percentage = previous

    def _normalize_test_cases(self, test_cases: list[dict]) -> list[CodingTestCase]:
        normalized = []
        total_bytes = 0
        for item in test_cases:
            if not isinstance(item, dict):
                raise ValueError('test cases must contain input and expected output strings')
            input_value = item.get('input', '')
            output_value = item.get('expected_output', '')
            if not isinstance(input_value, str) or not isinstance(output_value, str):
                raise ValueError('test cases must contain input and expected output strings')
            if '\x00' in input_value or '\x00' in output_value:
                raise ValueError('test case data cannot contain NUL characters')
            try:
                input_size = len(input_value.encode('utf-8'))
                output_size = len(output_value.encode('utf-8'))
            except UnicodeEncodeError as exc:
                raise ValueError('test case data must be valid UTF-8') from exc
            if input_size > MAX_TEST_INPUT_BYTES:
                raise ValueError('test input exceeds the 100 KB limit')
            if output_size > MAX_TEST_OUTPUT_BYTES:
                raise ValueError('expected output exceeds the 64 KB limit')
            total_bytes += input_size + output_size
            normalized.append(CodingTestCase(input=input_value, expected_output=output_value))
        if total_bytes > 1_000_000:
            raise ValueError('combined test data exceeds the 1 MB limit')
        return normalized


def get_coding_service() -> CodingChallengeService:
    service = current_app.extensions.get('coding_service')
    if service is None:
        service = CodingChallengeService()
        current_app.extensions['coding_service'] = service
    return service
