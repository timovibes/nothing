"""
Notification model — every email we send (or attempt to send), regardless of the underlying
provider, with delivery status and error tracking.
"""

import enum
import uuid

from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, func, Text
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class NotificationChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"  # not implemented yet — reserved for a future SMS adapter (e.g. Africa's Talking)


class NotificationStatus(str, enum.Enum):
    SENT = "sent"
    FAILED = "failed"


class NotificationType(str, enum.Enum):
    PAYMENT_RECEIPT = "payment_receipt"
    PAYMENT_DECLINED = "payment_declined"
    REFUND_CONFIRMATION = "refund_confirmation"
    PAYOUT_PAID = "payout_paid"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True, index=True)

    channel = Column(Enum(NotificationChannel), nullable=False, default=NotificationChannel.EMAIL)
    notification_type = Column(Enum(NotificationType), nullable=False)

    recipient = Column(String(255), nullable=False)  # email address (or phone number, once SMS exists)
    subject = Column(String(255), nullable=True)
    body = Column(Text, nullable=False)

    status = Column(Enum(NotificationStatus), nullable=False, default=NotificationStatus.SENT)
    error_message = Column(String(1000), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)