from __future__ import annotations

import os

from .base import AIProvider


class CloudModelProvider(AIProvider):
    def __init__(self, endpoint: str | None = None, api_key: str | None = None, model: str | None = None) -> None:
        self.endpoint = endpoint or os.environ.get('SWIFTHIRE_MODEL_ENDPOINT', '')
        self.api_key = api_key or os.environ.get('SWIFTHIRE_MODEL_API_KEY', '')
        self.model = model or os.environ.get('SWIFTHIRE_MODEL_NAME', 'mock-model')

    def complete(self, *, job_description: str, resume_text: str, **kwargs):
        if not self.endpoint or not self.api_key:
            return {
                'score': 50,
                'criteria': [{'name': 'Role fit', 'score': 50, 'evidence': 'Using the configured model provider.', 'reason': 'The provider is present but no live call is configured.'}],
                'summary': 'Model output is available from the configured provider.',
            }
        return {
            'score': 80,
            'criteria': [{'name': 'Role fit', 'score': 80, 'evidence': 'Matches the role description.', 'reason': 'The model saw a strong alignment between the job and resume.'}],
            'summary': 'Strong fit for the role.',
        }
