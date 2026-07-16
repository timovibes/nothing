"""
 refund business logic — validates the refund amount against what's already been refunded,
 posts the ledger reversal (fee stays with the platform), and can push a merchant's balance
 negative if needed.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.payment import PaymentIntentStatus
from app.models.ledger import LedgerAccountType, LedgerEntryDirection, LedgerEntryType
from app.repositories.payment_repository import PaymentRepository
from app.repositories.refund_repository import RefundRepository
from app.repositories.ledger_repository import LedgerRepository
from app.schemas.refund import RefundCreateRequest
from app.services.webhook_service import WebhookService


class RefundService:
    def __init__(self, db: Session):
        self.db = db
        self.payment_repo = PaymentRepository(db)
        self.refund_repo = RefundRepository(db)
        self.ledger_repo = LedgerRepository(db)
        self.webhook_service = WebhookService(db)
    def create_refund(self, merchant_id: uuid.UUID, payment_intent_id: uuid.UUID, payload: RefundCreateRequest):
        intent = self.payment_repo.get_payment_intent(merchant_id, payment_intent_id)
        if intent is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment intent not found")

        if intent.status != PaymentIntentStatus.SUCCEEDED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot refund a payment intent in status '{intent.status.value}' — only 'succeeded' payments can be refunded",
            )

        already_refunded = self.refund_repo.get_total_refunded(payment_intent_id)
        remaining_refundable = intent.amount_minor - already_refunded

        refund_amount = payload.amount_minor if payload.amount_minor is not None else remaining_refundable

        if refund_amount <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Refund amount must be greater than zero")

        if refund_amount > remaining_refundable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Refund amount ({refund_amount}) exceeds remaining refundable amount ({remaining_refundable})",
            )

        transaction_group_id = uuid.uuid4()

        # Leg 1: platform cash decreases (credit) — money is leaving the platform back to the customer's card
        self.ledger_repo.add_entry(
            transaction_group_id=transaction_group_id,
            account_type=LedgerAccountType.PLATFORM_CASH,
            direction=LedgerEntryDirection.CREDIT,
            amount_minor=refund_amount,
            currency=intent.currency,
            entry_type=LedgerEntryType.REFUND,
            merchant_id=merchant_id,
            reference_id=payment_intent_id,
            description="Funds returned to customer via refund",
        )

        # Leg 2: merchant_payable decreases (debit) by the FULL refund amount — the platform's
        # original fee is NOT reversed, so the merchant absorbs it. This can push their payable
        # (and available balance) negative, which is recovered from their next payout.
        self.ledger_repo.add_entry(
            transaction_group_id=transaction_group_id,
            account_type=LedgerAccountType.MERCHANT_PAYABLE,
            direction=LedgerEntryDirection.DEBIT,
            amount_minor=refund_amount,
            currency=intent.currency,
            entry_type=LedgerEntryType.REFUND,
            merchant_id=merchant_id,
            reference_id=payment_intent_id,
            description="Merchant payable reduced by full refund amount; platform fee not reversed",
        )

        refund = self.refund_repo.create_refund(
            payment_intent_id=payment_intent_id,
            merchant_id=merchant_id,
            amount_minor=refund_amount,
            currency=intent.currency,
            reason=payload.reason,
            ledger_transaction_group_id=transaction_group_id,
        )

        # This can legitimately go negative — that's intentional, see comment above
        self.ledger_repo.debit_wallet_for_refund(merchant_id, intent.currency, refund_amount)

        self.db.commit()
        self.db.refresh(refund)

        self.webhook_service.emit_event(
            merchant_id,
            "payment_intent.refunded",
            {
                "payment_intent_id": str(payment_intent_id),
                "refund_id": str(refund.id),
                "amount_minor": refund_amount,
                "currency": intent.currency,
            },
        )

        return refund

    def list_refunds_for_intent(self, merchant_id: uuid.UUID, payment_intent_id: uuid.UUID):
        intent = self.payment_repo.get_payment_intent(merchant_id, payment_intent_id)
        if intent is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment intent not found")
        return self.refund_repo.list_for_intent(payment_intent_id)