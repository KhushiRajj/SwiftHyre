from __future__ import annotations

from .base import EmailSender, SendResult


class ResendEmailSender(EmailSender):
    def send(self, to: str, subject: str, text: str, idempotency_key: str) -> SendResult:
        if not to or not subject or not text:
            return SendResult(status='failed', error='invalid email payload')
        return SendResult(status='sent', message_id=f'resend-{idempotency_key}')
