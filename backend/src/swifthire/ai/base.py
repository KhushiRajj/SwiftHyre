from __future__ import annotations

from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    def complete(self, *, job_description: str, resume_text: str, **kwargs):
        raise NotImplementedError
