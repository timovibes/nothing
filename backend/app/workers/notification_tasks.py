"""
Celery task wrapper so sending an email never blocks the request that triggered it
(same reasoning as webhook delivery — Gmail's SMTP server being slow shouldn't delay a
payment confirmation response).
"""

import uuid

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.notification_service import NotificationService
from app.models.notification import NotificationType


@celery_app.task(name="app.workers.notification_tasks.send_notification_task")
def send_notification_task(
    merchant_id: str,
    notification_type: str,
    recipient_email: str,
    subject: str,
    body: str,
    customer_id: str | None = None,
):
    db = SessionLocal()
    try:
        service = NotificationService(db)
        service.send_notification(
            merchant_id=uuid.UUID(merchant_id),
            notification_type=NotificationType(notification_type),
            recipient_email=recipient_email,
            subject=subject,
            body=body,
            customer_id=uuid.UUID(customer_id) if customer_id else None,
        )
    finally:
        db.close()