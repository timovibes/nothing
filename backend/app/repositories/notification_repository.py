"""
direct database queries for creating and listing notification records
"""

import uuid

from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationChannel, NotificationType, NotificationStatus


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        merchant_id: uuid.UUID,
        notification_type: NotificationType,
        recipient: str,
        subject: str,
        body: str,
        status: NotificationStatus,
        customer_id: uuid.UUID | None = None,
        error_message: str | None = None,
        channel: NotificationChannel = NotificationChannel.EMAIL,
    ) -> Notification:
        notification = Notification(
            merchant_id=merchant_id,
            customer_id=customer_id,
            channel=channel,
            notification_type=notification_type,
            recipient=recipient,
            subject=subject,
            body=body,
            status=status,
            error_message=error_message,
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def list_for_merchant(self, merchant_id: uuid.UUID) -> list[Notification]:
        return (
            self.db.query(Notification)
            .filter(Notification.merchant_id == merchant_id)
            .order_by(Notification.created_at.desc())
            .all()
        )