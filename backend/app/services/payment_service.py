"""
the actual payment business logic — tokenizing cards, creating intents, confirming/authorizing
them through the processor adapter, and idempotency handling.
"""
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.payment import PaymentIntentStatus
from app.repositories.payment_repository import PaymentRepository
from app.services.processor_adapter import get_processor_adapter, AuthorizationOutcome
from app.schemas.payment import TokenizeCardRequest, PaymentIntentCreateRequest
from app.services.ledger_service import LedgerService


class PaymentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PaymentRepository(db)
        self.processor = get_processor_adapter()
        self.ledger_service = LedgerService(db)

    def tokenize_card(self, merchant_id: uuid.UUID, payload: TokenizeCardRequest):
        result = self.processor.tokenize_card(
            card_number=payload.card_number,
            exp_month=payload.exp_month,
            exp_year=payload.exp_year,
            cvv=payload.cvv,
        )
        return self.repo.create_payment_method(
            merchant_id=merchant_id,
            token=result.token,
            card_brand=result.card_brand,
            card_last4=result.card_last4,
            exp_month=payload.exp_month,
            exp_year=payload.exp_year,
        )

    def create_intent(self, merchant_id: uuid.UUID, is_live_mode: bool, payload: PaymentIntentCreateRequest):
        if payload.idempotency_key:
            existing = self.repo.find_by_idempotency_key(merchant_id, payload.idempotency_key)
            if existing is not None:
                return existing

        return self.repo.create_payment_intent(
            merchant_id=merchant_id,
            amount_minor=payload.amount_minor,
            currency=payload.currency.upper(),
            description=payload.description,
            idempotency_key=payload.idempotency_key,
            is_live_mode="live" if is_live_mode else "test",
        )

    def get_intent(self, merchant_id: uuid.UUID, intent_id: uuid.UUID):
        intent = self.repo.get_payment_intent(merchant_id, intent_id)
        if intent is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment intent not found")
        return intent

    def list_intents(self, merchant_id: uuid.UUID):
        return self.repo.list_for_merchant(merchant_id)

    def confirm_intent(self, merchant_id: uuid.UUID, intent_id: uuid.UUID, payment_method_id: uuid.UUID):
        intent = self.get_intent(merchant_id, intent_id)

        if intent.status != PaymentIntentStatus.REQUIRES_PAYMENT_METHOD:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot confirm a payment intent in status '{intent.status.value}'",
            )

        payment_method = self.repo.get_payment_method(merchant_id, payment_method_id)
        if payment_method is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")

        # Mark as processing before calling out to the processor
        intent = self.repo.update_status(intent, PaymentIntentStatus.PROCESSING, payment_method_id=payment_method.id)

        result = self.processor.authorize(
            amount_minor=intent.amount_minor,
            currency=intent.currency,
            payment_method_token=payment_method.token,
        )

        if result.outcome == AuthorizationOutcome.APPROVED:
            intent = self.repo.update_status(intent, PaymentIntentStatus.SUCCEEDED)
            # Only a genuinely successful payment gets posted to the ledger
            self.ledger_service.record_successful_payment(
                merchant_id=merchant_id,
                payment_intent_id=intent.id,
                amount_minor=intent.amount_minor,
                currency=intent.currency,
            )
        elif result.outcome == AuthorizationOutcome.DECLINED:
            intent = self.repo.update_status(intent, PaymentIntentStatus.DECLINED, failure_reason=result.failure_reason)
        else:  # TIMEOUT
            intent = self.repo.update_status(intent, PaymentIntentStatus.PROCESSING, failure_reason=result.failure_reason)

        return intent