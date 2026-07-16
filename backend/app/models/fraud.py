"""
blacklist tables (hard-block gate), RiskAssessment (every scoring decision, for audit/tuning
later), and FraudCase (the manual review queue itself).
"""

import enum
import uuid

from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class FraudCaseStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class BlacklistedCard(Base):
    __tablename__ = "blacklisted_cards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Nullable merchant_id: null = platform-wide block, set = this merchant's own block list
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=True, index=True)

    # Simple fingerprint: last4 + exp_month + exp_year, not the full card number — lets a merchant
    # block a known-bad card even before it's ever been tokenized in our system.
    card_fingerprint = Column(String(32), nullable=False, index=True)
    reason = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class BlacklistedIP(Base):
    __tablename__ = "blacklisted_ips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=True, index=True)

    ip_address = Column(String(45), nullable=False, index=True)  # IPv4 or IPv6
    reason = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_intent_id = Column(UUID(as_uuid=True), ForeignKey("payment_intents.id"), nullable=False, index=True)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=False, index=True)

    score = Column(Integer, nullable=False)
    reasons = Column(JSONB, nullable=False)  # list[str] — e.g. ["high_value_amount", "velocity_exceeded"]

    device_fingerprint = Column(String(64), nullable=True)
    ip_address = Column(String(45), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class FraudCase(Base):
    __tablename__ = "fraud_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_intent_id = Column(UUID(as_uuid=True), ForeignKey("payment_intents.id"), nullable=False, index=True, unique=True)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=False, index=True)

    risk_score = Column(Integer, nullable=False)
    status = Column(Enum(FraudCaseStatus), nullable=False, default=FraudCaseStatus.PENDING)

    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)