"""
Refund model — tracks each refund (full or partial) against a payment intent, independent
of the intent's own status field.
"""

import enum
import uuid

from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class RefundStatus(str, enum.Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Refund(Base):
    __tablename__ = "refunds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_intent_id = Column(UUID(as_uuid=True), ForeignKey("payment_intents.id"), nullable=False, index=True)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=False, index=True)

    amount_minor = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=False)

    status = Column(Enum(RefundStatus), nullable=False, default=RefundStatus.SUCCEEDED)
    reason = Column(String(500), nullable=True)

    # The ledger transaction group that recorded the merchant_payable debit / platform_cash credit for this refund
    ledger_transaction_group_id = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    payment_intent = relationship("PaymentIntent")