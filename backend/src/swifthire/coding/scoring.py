from __future__ import annotations

from .runner import CodeRunner, RunnerProvider


class ChallengeScorer:
    def __init__(self, runner: RunnerProvider | None = None) -> None:
        self.runner = runner or CodeRunner()

    def score(self, challenge, source: str, language: str) -> dict:
        total = len(challenge.private_test_cases)
        if total == 0:
            return {'score_percentage': None, 'status': 'invalid'}

        passed = 0
        for case in challenge.private_test_cases:
            result = self.runner.run(source, language, case.input, 10)
            if result.status != 'completed':
                return {
                    'score_percentage': None,
                    'status': result.status,
                }
            if result.exit_code == 0 and result.stdout.strip() == case.expected_output.strip():
                passed += 1

        score = int((passed / total) * 100)
        return {
            'score_percentage': score,
            'status': 'completed' if score == 100 else 'partial',
        }
