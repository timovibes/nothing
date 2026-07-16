"""direct database queries for creating and updating payout records."""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.settlement import Payout, PayoutStatus
from app.models.ledger import WalletBalance


class SettlementRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_wallets_with_positive_balance(self) -> list[WalletBalance]:
        return self.db.query(WalletBalance).filter(WalletBalance.available_balance_minor > 0).all()

    def create_payout(
        self,
        merchant_id: uuid.UUID,
        amount_minor: int,
        currency: str,
        expected_arrival_at: datetime,
        ledger_transaction_group_id: uuid.UUID,
    ) -> Payout:
        payout = Payout(
            merchant_id=merchant_id,
            amount_minor=amount_minor,
            currency=currency,
            status=PayoutStatus.IN_TRANSIT,
            expected_arrival_at=expected_arrival_at,
            ledger_transaction_group_id=ledger_transaction_group_id,
        )
        self.db.add(payout)
        return payout

    def get_due_in_transit_payouts(self, ignore_date_check: bool = False) -> list[Payout]:
        query = self.db.query(Payout).filter(Payout.status == PayoutStatus.IN_TRANSIT)
        if not ignore_date_check:
            query = query.filter(Payout.expected_arrival_at <= datetime.now(timezone.utc))
        return query.all()

    def mark_paid(self, payout: Payout) -> Payout:
        payout.status = PayoutStatus.PAID
        payout.paid_at = datetime.now(timezone.utc)
        self.db.add(payout)
        return payout

    def list_for_merchant(self, merchant_id: uuid.UUID) -> list[Payout]:
        return (
            self.db.query(Payout)
            .filter(Payout.merchant_id == merchant_id)
            .order_by(Payout.initiated_at.desc())
            .all()
        )