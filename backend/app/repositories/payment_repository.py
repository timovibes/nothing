"""
direct database queries for payment methods and payment intents.
"""

import uuid

from sqlalchemy.orm import Session

from app.models.payment import PaymentMethod, PaymentIntent, PaymentIntentStatus


class PaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_payment_method(
        self,
        merchant_id: uuid.UUID,
        token: str,
        card_brand: str,
        card_last4: str,
        exp_month: int,
        exp_year: int,
    ) -> PaymentMethod:
        pm = PaymentMethod(
            merchant_id=merchant_id,
            token=token,
            card_brand=card_brand,
            card_last4=card_last4,
            card_exp_month=exp_month,
            card_exp_year=exp_year,
        )
        self.db.add(pm)
        self.db.commit()
        self.db.refresh(pm)
        return pm

    def get_payment_method(self, merchant_id: uuid.UUID, payment_method_id: uuid.UUID) -> PaymentMethod | None:
        return (
            self.db.query(PaymentMethod)
            .filter(PaymentMethod.id == payment_method_id, PaymentMethod.merchant_id == merchant_id)
            .first()
        )

    def find_by_idempotency_key(self, merchant_id: uuid.UUID, idempotency_key: str) -> PaymentIntent | None:
        return (
            self.db.query(PaymentIntent)
            .filter(PaymentIntent.merchant_id == merchant_id, PaymentIntent.idempotency_key == idempotency_key)
            .first()
        )

    def create_payment_intent(
        self,
        merchant_id: uuid.UUID,
        amount_minor: int,
        currency: str,
        description: str | None,
        idempotency_key: str | None,
        is_live_mode: str,
        customer_id: uuid.UUID | None = None,
    ) -> PaymentIntent:
        intent = PaymentIntent(
            merchant_id=merchant_id,
            customer_id=customer_id,
            amount_minor=amount_minor,
            currency=currency,
            description=description,
            idempotency_key=idempotency_key,
            is_live_mode=is_live_mode,
            status=PaymentIntentStatus.REQUIRES_PAYMENT_METHOD,
        )
        self.db.add(intent)
        self.db.commit()
        self.db.refresh(intent)
        return intent

    def get_payment_intent(self, merchant_id: uuid.UUID, intent_id: uuid.UUID) -> PaymentIntent | None:
        return (
            self.db.query(PaymentIntent)
            .filter(PaymentIntent.id == intent_id, PaymentIntent.merchant_id == merchant_id)
            .first()
        )

    def update_status(
        self,
        intent: PaymentIntent,
        status: PaymentIntentStatus,
        payment_method_id: uuid.UUID | None = None,
        failure_reason: str | None = None,
    ) -> PaymentIntent:
        intent.status = status
        if payment_method_id is not None:
            intent.payment_method_id = payment_method_id
        intent.failure_reason = failure_reason
        self.db.add(intent)
        self.db.commit()
        self.db.refresh(intent)
        return intent

    def list_for_merchant(self, merchant_id: uuid.UUID, limit: int = 50) -> list[PaymentIntent]:
        return (
            self.db.query(PaymentIntent)
            .filter(PaymentIntent.merchant_id == merchant_id)
            .order_by(PaymentIntent.created_at.desc())
            .limit(limit)
            .all()
        )


    def get_payment_intent_by_client_secret(self, intent_id: uuid.UUID, client_secret: str) -> PaymentIntent | None:
            return (
                self.db.query(PaymentIntent)
                .filter(PaymentIntent.id == intent_id, PaymentIntent.client_secret == client_secret)
                .first()
            )