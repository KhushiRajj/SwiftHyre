from __future__ import annotations

from typing import Any

from flask import current_app

from ..applications.service import get_application_service
from ..assessments.service import get_assessment_service
from ..coding.models import CodingChallenge
from ..coding.service import CodingChallengeService, get_coding_service
from ..jobs.service import get_job_service
from ..workflow.service import get_workflow_service
from .schemas import ResultState


class ReportingService:
    def get_job_dashboard(self, job_id: str, recruiter_id: str) -> dict[str, Any] | None:
        job = get_job_service().get_by_id(job_id)
        if job is None or job.recruiter_id != recruiter_id:
            return None

        applications = get_application_service().list_for_job(job_id)
        assessment_service = get_assessment_service()
        coding_service = get_coding_service()
        workflow_service = get_workflow_service()
        coding_challenges = coding_service.list_for_job(job_id)
        counts_by_status: dict[str, int] = {}
        candidates: list[dict] = []
        for application in applications:
            status = application.status
            counts_by_status[status] = counts_by_status.get(status, 0) + 1

            match_result = {
                'state': 'pending',
                'score': None,
                'criteria': [],
                'summary': None,
            }
            assessments = {
                assessment.stage: assessment
                for assessment in assessment_service.get_application_assessments(application.id)
            }
            stage_results: list[dict[str, Any]] = []
            for stage in job.stage_order:
                if stage == 'online_assessment':
                    assessment = assessments.get(stage)
                    if assessment is None:
                        result = self._empty_result(stage, 'pending')
                    elif assessment.status == 'submitted' and assessment.score is not None:
                        result = {
                            'stage_key': stage,
                            'state': 'completed',
                            'score': assessment.score,
                            'criteria': [],
                            'summary': 'Assessment submitted.',
                        }
                    elif assessment.status == 'not_sent':
                        result = self._empty_result(stage, 'unavailable')
                    elif assessment.status == 'pending_review':
                        result = self._empty_result(stage, 'pending')
                    else:
                        result = self._empty_result(stage, 'failed')
                elif stage == 'coding_assessment':
                    result = self._coding_stage_result(coding_service, coding_challenges, application.id)
                else:
                    result = self._empty_result(stage, 'not_configured')
                stage_results.append(result)

            decision_history = [
                {
                    'decision': decision.decision,
                    'expected_stage': decision.expected_stage,
                    'timestamp': decision.created_at,
                }
                for decision in workflow_service.list_decisions_for_application(application.id)
            ]

            current_stage = getattr(application, 'current_stage', None)
            available_actions = []
            if status != 'rejected' and current_stage in job.stage_order:
                current_stage_index = job.stage_order.index(current_stage)
                if current_stage_index + 1 < len(job.stage_order):
                    available_actions.append({
                        'decision': 'advance',
                        'expected_stage': current_stage,
                    })
                available_actions.append({
                    'decision': 'reject',
                    'expected_stage': current_stage,
                })
            notification_states = {stage: 'not_applicable' for stage in job.stage_order}

            candidates.append({
                'application_id': application.id,
                'candidate_name': application.applicant_name,
                'status': application.status,
                'current_stage': current_stage,
                'match_result': match_result,
                'stage_results': stage_results,
                'decision_history': decision_history,
                'available_actions': available_actions,
                'notification_states': notification_states,
            })

        counts = {
            'total': len(applications),
            'by_status': counts_by_status,
        }

        return {
            'job': {
                'id': job.id,
                'title': job.title,
                'status': job.status,
            },
            'counts': counts,
            'candidates': candidates,
        }

    @staticmethod
    def _empty_result(stage_key: str, state: ResultState) -> dict[str, Any]:
        return {
            'stage_key': stage_key,
            'state': state,
            'score': None,
            'criteria': [],
            'summary': None,
        }

    @classmethod
    def _coding_stage_result(
        cls,
        coding_service: CodingChallengeService,
        challenges: list[CodingChallenge],
        application_id: str,
    ) -> dict[str, Any]:
        if not challenges:
            return cls._empty_result('coding_assessment', 'not_configured')

        submissions = [
            coding_service.get_submission_for_application(challenge.id, application_id)
            for challenge in challenges
        ]
        result_states: list[ResultState] = []
        criteria: list[dict[str, Any]] = []
        scores: list[int] = []
        for challenge, submission in zip(challenges, submissions):
            if submission is None:
                result_states.append('pending')
                continue
            if submission.status in {'completed', 'partial'} and submission.score_percentage is not None:
                result_states.append('completed')
                scores.append(submission.score_percentage)
                criteria.append({
                    'name': challenge.title,
                    'score': submission.score_percentage,
                    'evidence': 'Automated test cases completed.',
                })
            elif submission.status == 'processing':
                result_states.append('pending')
            elif submission.status in {'unavailable', 'timeout'}:
                result_states.append('unavailable')
            elif submission.status == 'invalid':
                result_states.append('failed')
            else:
                result_states.append('failed')

        if 'unavailable' in result_states:
            state = 'unavailable'
        elif 'failed' in result_states:
            state = 'failed'
        elif 'pending' in result_states:
            state = 'pending'
        else:
            state = 'completed'

        score = round(sum(scores) / len(challenges)) if state == 'completed' else None
        summary = None
        if state == 'completed':
            summary = f'Average score across {len(challenges)} coding challenge(s).'
        elif state == 'pending':
            summary = 'Waiting for coding challenge submissions.'
        elif state == 'unavailable':
            summary = 'A coding challenge could not be scored.'
        elif state == 'failed':
            summary = 'A coding challenge result is invalid.'

        return {
            'stage_key': 'coding_assessment',
            'state': state,
            'score': score,
            'criteria': criteria,
            'summary': summary,
        }


def get_reporting_service() -> ReportingService:
    service = current_app.extensions.get('reporting_service')
    if service is None:
        service = ReportingService()
        current_app.extensions['reporting_service'] = service
    return service
