"""
 the four audit tables — automatic API call log, automatic mutation log, lightweight user
 activity trail, and per-login session records.
"""

import enum
import uuid

from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, func, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class ActorType(str, enum.Enum):
    USER = "user"              # a dashboard-logged-in human (via JWT)
    MERCHANT_API_KEY = "merchant_api_key"  # a merchant's backend calling via sk_test/sk_live
    SYSTEM = "system"          # background jobs (Celery tasks) acting without a human/API key
    ANONYMOUS = "anonymous"    # unauthenticated request (e.g. failed login attempt)


class ApiLog(Base):
    __tablename__ = "api_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=True, index=True)

    method = Column(String(10), nullable=False)
    path = Column(String(500), nullable=False)
    status_code = Column(Integer, nullable=False)
    latency_ms = Column(Float, nullable=False)
    ip_address = Column(String(45), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    actor_type = Column(Enum(ActorType), nullable=False)
    actor_id = Column(UUID(as_uuid=True), nullable=True)  # user_id or merchant_id, depending on actor_type
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=True, index=True)

    action = Column(String(20), nullable=False)   # HTTP method: POST, PUT, PATCH, DELETE
    entity_type = Column(String(100), nullable=False)  # e.g. "merchants", "payment-intents", "refunds"
    entity_id = Column(UUID(as_uuid=True), nullable=True)  # parsed from the URL path, if present

    request_body = Column(JSONB, nullable=True)  # sanitized — passwords/card numbers/CVVs stripped
    status_code = Column(Integer, nullable=False)
    ip_address = Column(String(45), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    activity_type = Column(String(100), nullable=False)  # e.g. "login", "viewed_profile"
    activity_metadata = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LoginSession(Base):
    __tablename__ = "login_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)  # null if email didn't even match a user

    email_attempted = Column(String(255), nullable=False)
    ip_address = Column(String(45), nullable=True)
    device = Column(String(500), nullable=True)  # raw User-Agent string
    success = Column(Boolean, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)