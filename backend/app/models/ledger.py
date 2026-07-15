"""
the double-entry LedgerEntry model (one row per debit/credit) plus a WalletBalance
model that tracks each merchant's running available balance derived from those entries.
"""

import enum
import uuid

from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class LedgerAccountType(str, enum.Enum):
    PLATFORM_CASH = "platform_cash"          # asset: money the processor has actually deposited with us
    MERCHANT_PAYABLE = "merchant_payable"    # liability: what we owe a specific merchant
    PLATFORM_REVENUE = "platform_revenue"    # income: our fee, recognized on success


class LedgerEntryDirection(str, enum.Enum):
    DEBIT = "debit"
    CREDIT = "credit"


class LedgerEntryType(str, enum.Enum):
    PAYMENT_SETTLEMENT = "payment_settlement"
    REFUND = "refund"
    PAYOUT = "payout"
    ADJUSTMENT = "adjustment"


class LedgerEntry(Base):
    """
    One row = one leg (debit OR credit) of a double-entry transaction.
    A single payment produces multiple LedgerEntry rows sharing the same transaction_group_id,
    and the sum of debits in that group must always equal the sum of credits.
    """
    __tablename__ = "ledger_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Groups all legs of one accounting transaction together (e.g. one payment = 3 rows, same group id)
    transaction_group_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    account_type = Column(Enum(LedgerAccountType), nullable=False)
    # Which merchant this entry belongs to. Null for pure platform-internal accounts (e.g. platform_cash, platform_revenue
    # are still tagged per-merchant here so we can trace exactly which payment generated them).
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=True, index=True)

    direction = Column(Enum(LedgerEntryDirection), nullable=False)
    amount_minor = Column(Integer, nullable=False)  # always positive; direction determines debit vs credit
    currency = Column(String(3), nullable=False)

    entry_type = Column(Enum(LedgerEntryType), nullable=False)
    reference_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # e.g. the payment_intent.id this came from
    description = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class WalletBalance(Base):
    """
    Denormalized running balance per merchant, per currency — avoids summing the entire
    ledger_entries table on every balance check. Updated transactionally alongside ledger writes.
    """
    __tablename__ = "wallet_balances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=False, index=True)
    currency = Column(String(3), nullable=False)

    # Funds recognized as owed to the merchant but not yet paid out (settled) to their bank account
    available_balance_minor = Column(Integer, nullable=False, default=0)
    # Funds already scheduled/paid out — kept for auditing, doesn't reduce available_balance retroactively
    total_settled_minor = Column(Integer, nullable=False, default=0)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    merchant = relationship("Merchant")