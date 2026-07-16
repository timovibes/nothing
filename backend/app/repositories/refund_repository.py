"""
direct database queries for creating refunds and computing how much of a payment intent has
already been refunded.
"""

import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.refund import Refund, RefundStatus


class RefundRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_total_refunded(self, payment_intent_id: uuid.UUID) -> int:
        total = (
            self.db.query(func.coalesce(func.sum(Refund.amount_minor), 0))
            .filter(Refund.payment_intent_id == payment_intent_id, Refund.status == RefundStatus.SUCCEEDED)
            .scalar()
        )
        return int(total or 0)

    def create_refund(
        self,
        payment_intent_id: uuid.UUID,
        merchant_id: uuid.UUID,
        amount_minor: int,
        currency: str,
        reason: str | None,
        ledger_transaction_group_id: uuid.UUID,
    ) -> Refund:
        refund = Refund(
            payment_intent_id=payment_intent_id,
            merchant_id=merchant_id,
            amount_minor=amount_minor,
            currency=currency,
            status=RefundStatus.SUCCEEDED,
            reason=reason,
            ledger_transaction_group_id=ledger_transaction_group_id,
        )
        self.db.add(refund)
        return refund

    def list_for_intent(self, payment_intent_id: uuid.UUID) -> list[Refund]:
        return (
            self.db.query(Refund)
            .filter(Refund.payment_intent_id == payment_intent_id)
            .order_by(Refund.created_at.desc())
            .all()
        )