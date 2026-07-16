"""
the four webhook tables — registered endpoints, generated events, per-endpoint delivery
attempts with retry state, and raw request/response logs for debugging.
"""

import enum
import uuid

from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, func, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship

from app.core.database import Base


class WebhookDeliveryStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"        # this specific attempt failed, may retry
    EXHAUSTED = "exhausted"  # all retries used up, permanently failed


class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=False, index=True)

    url = Column(String(2048), nullable=False)
    # Used to HMAC-sign every payload we send, so the merchant can verify it really came from us
    signing_secret = Column(String(255), nullable=False)

    # e.g. ["payment_intent.succeeded", "payment_intent.refunded", "payout.paid"] — empty list = subscribe to all
    subscribed_events = Column(ARRAY(String), nullable=False, default=list)

    is_active = Column(String(10), nullable=False, default="active")  # "active" or "disabled"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=False, index=True)

    event_type = Column(String(100), nullable=False, index=True)  # e.g. "payment_intent.succeeded"
    payload = Column(JSONB, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    webhook_event_id = Column(UUID(as_uuid=True), ForeignKey("webhook_events.id"), nullable=False, index=True)
    webhook_endpoint_id = Column(UUID(as_uuid=True), ForeignKey("webhook_endpoints.id"), nullable=False, index=True)

    status = Column(Enum(WebhookDeliveryStatus), nullable=False, default=WebhookDeliveryStatus.PENDING)
    attempt_count = Column(Integer, nullable=False, default=0)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    last_attempted_at = Column(DateTime(timezone=True), nullable=True)
    last_response_status_code = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    webhook_event = relationship("WebhookEvent")
    webhook_endpoint = relationship("WebhookEndpoint")


class WebhookLog(Base):
    __tablename__ = "webhook_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    webhook_delivery_id = Column(UUID(as_uuid=True), ForeignKey("webhook_deliveries.id"), nullable=False, index=True)

    request_body = Column(Text, nullable=True)
    response_status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    error_message = Column(String(1000), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)