from __future__ import annotations

import random
from typing import Any

from flask import current_app

from ..applications.service import get_application_service
from ..jobs.service import get_job_service
from .models import Assessment, AssessmentQuestion

QUESTION_BANK = [
    ('What is the primary goal of user research?', ['A', 'B', 'C', 'D'], 'A'),
    ('Which practice best reduces design churn?', ['A', 'B', 'C', 'D'], 'B'),
    ('What does a strong product brief include?', ['A', 'B', 'C', 'D'], 'C'),
    ('Which metric best tracks product adoption?', ['A', 'B', 'C', 'D'], 'D'),
    ('Which statement best describes a sprint review?', ['A', 'B', 'C', 'D'], 'A'),
    ('A well-scoped experiment should do what?', ['A', 'B', 'C', 'D'], 'B'),
    ('Which task is most aligned to a design lead role?', ['A', 'B', 'C', 'D'], 'C'),
    ('Which signal indicates strong stakeholder alignment?', ['A', 'B', 'C', 'D'], 'D'),
    ('What is the most useful outcome of usability testing?', ['A', 'B', 'C', 'D'], 'A'),
    ('Which artifact best supports prioritization?', ['A', 'B', 'C', 'D'], 'B'),
]


class AssessmentService:
    def __init__(self) -> None:
        self._assessments_by_id: dict[str, Assessment] = {}
        self._assessments_by_token: dict[str, Assessment] = {}
        self._assessments_by_application: dict[str, list[Assessment]] = {}

    def create_assessment(self, application_id: str, job_id: str, stage: str) -> Assessment:
        assessment = Assessment.create(application_id, job_id, stage)
        self._assessments_by_id[assessment.id] = assessment
        self._assessments_by_token[assessment.token] = assessment
        self._assessments_by_application.setdefault(application_id, []).append(assessment)

        pool = list(QUESTION_BANK)
        random.Random(assessment.id).shuffle(pool)
        assessment.questions = [
            AssessmentQuestion(
                id=f'q{index + 1}',
                prompt=prompt,
                choices=choices,
                answer=correct,
            )
            for index, (prompt, choices, correct) in enumerate(pool[:10])
        ]
        return assessment

    def get_by_token(self, token: str) -> Assessment | None:
        return self._assessments_by_token.get(token)

    def get_for_application(self, application_id: str) -> list[Assessment]:
        return list(self._assessments_by_application.get(application_id, []))

    def submit_answers(self, token: str, answers: dict[str, str]) -> Assessment:
        assessment = self.get_by_token(token)
        if assessment is None or assessment.used_token:
            raise LookupError('assessment not found')

        assessment.used_token = True
        assessment.answers = {key: str(value) for key, value in answers.items()}
        assessment.status = 'submitted'

        total = 0
        for question in assessment.questions:
            if assessment.answers.get(question.id) == question.answer:
                total += 1
        assessment.score = int((total / max(len(assessment.questions), 1)) * 100)
        return assessment

    def get_application_assessments(self, application_id: str) -> list[Assessment]:
        return self.get_for_application(application_id)


def get_assessment_service() -> AssessmentService:
    service = current_app.extensions.get('assessment_service')
    if service is None:
        service = AssessmentService()
        current_app.extensions['assessment_service'] = service
    return service
