#response schema for viewing notification history.
import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.notification import NotificationChannel, NotificationType, NotificationStatus


class NotificationResponse(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID | None
    channel: NotificationChannel
    notification_type: NotificationType
    recipient: str
    subject: str | None
    status: NotificationStatus
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}