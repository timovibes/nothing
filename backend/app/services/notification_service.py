"""
builds the subject/body for each notification type and sends it through the email
adapter, recording the outcome regardless of success or failure.
"""

import uuid

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.notification import NotificationType, NotificationStatus
from app.repositories.notification_repository import NotificationRepository
from app.services.email_adapter import get_email_adapter


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = NotificationRepository(db)
        self.email_adapter = get_email_adapter()

    def send_notification(
        self,
        merchant_id: uuid.UUID,
        notification_type: NotificationType,
        recipient_email: str,
        subject: str,
        body: str,
        customer_id: uuid.UUID | None = None,
    ):
        result = self.email_adapter.send(to_email=recipient_email, subject=subject, body=body)

        return self.repo.create(
            merchant_id=merchant_id,
            customer_id=customer_id,
            notification_type=notification_type,
            recipient=recipient_email,
            subject=subject,
            body=body,
            status=NotificationStatus.SENT if result.success else NotificationStatus.FAILED,
            error_message=result.error_message,
        )

    def list_notifications(self, merchant_id: uuid.UUID):
        return self.repo.list_for_merchant(merchant_id)


# --- Message builders — one function per notification type, kept separate from delivery logic ---

def build_payment_receipt(amount_minor: int, currency: str, description: str | None) -> tuple[str, str]:
    amount_display = f"{amount_minor / 100:.2f}"
    subject = f"Payment received: {currency} {amount_display}"
    body = (
        f"A payment of {currency} {amount_display} was successfully processed.\n"
        f"Description: {description or 'N/A'}\n\n"
        f"— nothing"
    )
    return subject, body


def build_payment_declined(amount_minor: int, currency: str, failure_reason: str | None) -> tuple[str, str]:
    amount_display = f"{amount_minor / 100:.2f}"
    subject = f"Payment declined: {currency} {amount_display}"
    body = (
        f"A payment attempt of {currency} {amount_display} was declined.\n"
        f"Reason: {failure_reason or 'unknown'}\n\n"
        f"— nothing"
    )
    return subject, body


def build_refund_confirmation(amount_minor: int, currency: str) -> tuple[str, str]:
    amount_display = f"{amount_minor / 100:.2f}"
    subject = f"Refund processed: {currency} {amount_display}"
    body = (
        f"A refund of {currency} {amount_display} has been processed.\n\n"
        f"— nothing"
    )
    return subject, body


def build_payout_paid(amount_minor: int, currency: str) -> tuple[str, str]:
    amount_display = f"{amount_minor / 100:.2f}"
    subject = f"Payout sent: {currency} {amount_display}"
    body = (
        f"Your payout of {currency} {amount_display} has been sent to your settlement bank account.\n\n"
        f"— nothing"
    )
    return subject, body