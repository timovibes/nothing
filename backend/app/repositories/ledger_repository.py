"""
direct database queries for writing ledger entries and reading/updating wallet balances.
"""

import uuid

from sqlalchemy.orm import Session

from app.models.ledger import LedgerEntry, WalletBalance, LedgerAccountType, LedgerEntryDirection, LedgerEntryType


class LedgerRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_entry(
        self,
        transaction_group_id: uuid.UUID,
        account_type: LedgerAccountType,
        direction: LedgerEntryDirection,
        amount_minor: int,
        currency: str,
        entry_type: LedgerEntryType,
        merchant_id: uuid.UUID | None = None,
        reference_id: uuid.UUID | None = None,
        description: str | None = None,
    ) -> LedgerEntry:
        entry = LedgerEntry(
            transaction_group_id=transaction_group_id,
            account_type=account_type,
            merchant_id=merchant_id,
            direction=direction,
            amount_minor=amount_minor,
            currency=currency,
            entry_type=entry_type,
            reference_id=reference_id,
            description=description,
        )
        self.db.add(entry)
        return entry

    def get_or_create_wallet(self, merchant_id: uuid.UUID, currency: str) -> WalletBalance:
        wallet = (
            self.db.query(WalletBalance)
            .filter(WalletBalance.merchant_id == merchant_id, WalletBalance.currency == currency)
            .first()
        )
        if wallet is None:
            wallet = WalletBalance(merchant_id=merchant_id, currency=currency, available_balance_minor=0, total_settled_minor=0)
            self.db.add(wallet)
            self.db.flush()
        return wallet

    def credit_wallet(self, merchant_id: uuid.UUID, currency: str, amount_minor: int) -> WalletBalance:
        wallet = self.get_or_create_wallet(merchant_id, currency)
        wallet.available_balance_minor += amount_minor
        self.db.add(wallet)
        return wallet

    def debit_wallet_for_settlement(self, merchant_id: uuid.UUID, currency: str, amount_minor: int) -> WalletBalance:
        wallet = self.get_or_create_wallet(merchant_id, currency)
        wallet.available_balance_minor -= amount_minor
        wallet.total_settled_minor += amount_minor
        self.db.add(wallet)
        return wallet
    
    def debit_wallet_for_refund(self, merchant_id: uuid.UUID, currency: str, amount_minor: int) -> WalletBalance:
        wallet = self.get_or_create_wallet(merchant_id, currency)
        wallet.available_balance_minor -= amount_minor
        self.db.add(wallet)
        return wallet

    def get_entries_for_transaction(self, transaction_group_id: uuid.UUID) -> list[LedgerEntry]:
        return self.db.query(LedgerEntry).filter(LedgerEntry.transaction_group_id == transaction_group_id).all()

    def get_entries_for_merchant(self, merchant_id: uuid.UUID, limit: int = 100) -> list[LedgerEntry]:
        return (
            self.db.query(LedgerEntry)
            .filter(LedgerEntry.merchant_id == merchant_id)
            .order_by(LedgerEntry.created_at.desc())
            .limit(limit)
            .all()
        )