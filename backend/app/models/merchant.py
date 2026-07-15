"""
full Merchant model (business profile, KYC state, settlement bank details) and ApiKey model
(test/live key pairs) — this file replaces merchant_stub.py entirely.
"""

import enum
import uuid

from sqlalchemy import Column, String, Boolean, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class KycStatus(str, enum.Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApiKeyType(str, enum.Enum):
    TEST_PUBLIC = "pk_test"
    TEST_SECRET = "sk_test"
    LIVE_PUBLIC = "pk_live"
    LIVE_SECRET = "sk_live"


class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    business_name = Column(String(255), nullable=False)
    business_email = Column(String(255), nullable=False)
    country = Column(String(2), nullable=False, default="KE")  # ISO 3166-1 alpha-2
    default_currency = Column(String(3), nullable=False, default="KES")

    kyc_status = Column(Enum(KycStatus), nullable=False, default=KycStatus.PENDING)
    kyc_rejection_reason = Column(String(500), nullable=True)

    # Settlement bank details — nullable until merchant fills them in, required before KYC can move to approved
    settlement_bank_name = Column(String(255), nullable=True)
    settlement_account_number = Column(String(64), nullable=True)
    settlement_account_name = Column(String(255), nullable=True)

    is_live_mode_enabled = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    api_keys = relationship("ApiKey", back_populates="merchant", cascade="all, delete-orphan")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=False, index=True)

    key_type = Column(Enum(ApiKeyType), nullable=False)
    display_prefix = Column(String(20), nullable=False)  # e.g. "sk_test_Ab3F9x" — shown in dashboard, never the full key
    hashed_key = Column(String(255), unique=True, nullable=False, index=True)

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    merchant = relationship("Merchant", back_populates="api_keys")