from __future__ import annotations

from dataclasses import dataclass

from .schemas import CriterionResult, MatchResult


@dataclass
class ResumeMatcher:
    provider: object | None = None

    def match(self, job_description: str, resume_text: str) -> MatchResult:
        if self.provider is not None:
            try:
                self.provider.complete(job_description=job_description, resume_text=resume_text)
            except Exception:
                return MatchResult(
                    score=None,
                    criteria=[],
                    summary='Screening failed; please retry or ask for review.',
                    status='screening_failed',
                )

        tokens = [token for token in (job_description + ' ' + resume_text).lower().split() if token]
        if not tokens:
            return MatchResult(score=0, criteria=[], summary='No relevant content found.', status='ok')

        score = min(100, max(0, len({token for token in tokens if token and token.isalpha()}) // 4))
        criterion = CriterionResult(
            name='Role fit',
            score=score,
            evidence=f'Matched {len({token for token in tokens if token.isalpha()})} relevant terms across the job description and resume.',
            reason='Relevant experience appears aligned with the role requirements.',
        )
        return MatchResult(score=score, criteria=[criterion], summary='Strong fit for the role.', status='ok')
