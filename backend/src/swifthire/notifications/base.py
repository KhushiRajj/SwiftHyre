from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SendResult:
    status: str
    message_id: str | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            'status': self.status,
            'message_id': self.message_id,
            'error': self.error,
        }


class EmailSender:
    def send(self, to: str, subject: str, text: str, idempotency_key: str) -> SendResult:
        raise NotImplementedError
