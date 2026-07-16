"""
Payout model tracking each sweep of a merchant's balance from in_transit to paid (or failed).
"""

import enum
import uuid

from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class PayoutStatus(str, enum.Enum):
    IN_TRANSIT = "in_transit"
    PAID = "paid"
    FAILED = "failed"


class Payout(Base):
    __tablename__ = "payouts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=False, index=True)

    amount_minor = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=False)

    status = Column(Enum(PayoutStatus), nullable=False, default=PayoutStatus.IN_TRANSIT)
    failure_reason = Column(String(255), nullable=True)

    # The ledger transaction group that recorded the merchant_payable debit / platform_cash credit for this payout
    ledger_transaction_group_id = Column(UUID(as_uuid=True), nullable=True)

    initiated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expected_arrival_at = Column(DateTime(timezone=True), nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    merchant = relationship("Merchant")