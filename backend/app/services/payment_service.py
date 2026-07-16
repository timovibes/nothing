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
from app.services.webhook_service import WebhookService
from app.services.notification_service import NotificationService, build_payment_receipt, build_payment_declined
from app.models.notification import NotificationType
from app.services.fraud_service import FraudService
from datetime import datetime, timedelta, timezone


class PaymentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PaymentRepository(db)
        self.processor = get_processor_adapter()
        self.ledger_service = LedgerService(db)
        self.webhook_service = WebhookService(db)
        self.notification_service = NotificationService(db)
        self.fraud_service = FraudService(db)

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
            customer_id=payload.customer_id,
        )

    def get_intent(self, merchant_id: uuid.UUID, intent_id: uuid.UUID):
        intent = self.repo.get_payment_intent(merchant_id, intent_id)
        if intent is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment intent not found")
        return intent

    def list_intents(self, merchant_id: uuid.UUID):
        return self.repo.list_for_merchant(merchant_id)

    def confirm_intent(
        self,
        merchant_id: uuid.UUID,
        intent_id: uuid.UUID,
        payment_method_id: uuid.UUID,
        device_fingerprint: str | None = None,
        billing_country: str | None = None,
        ip_address: str | None = None,
    ):
        intent = self.get_intent(merchant_id, intent_id)

        if intent.status != PaymentIntentStatus.REQUIRES_PAYMENT_METHOD:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot confirm a payment intent in status '{intent.status.value}'",
            )

        payment_method = self.repo.get_payment_method(merchant_id, payment_method_id)
        if payment_method is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")

        # --- Fraud gate: hard blacklist check, BEFORE authorization ever runs ---
        card_fingerprint = self.fraud_service.card_fingerprint(
            payment_method.card_last4, payment_method.card_exp_month, payment_method.card_exp_year
        )
        block_reason = self.fraud_service.check_blacklists(merchant_id, card_fingerprint, ip_address)
        if block_reason:
            intent = self.repo.update_status(intent, PaymentIntentStatus.DECLINED, failure_reason=block_reason)
            return intent

        # --- Risk scoring: soft gate, may route to manual review instead of processing ---
        velocity_exceeded = self.fraud_service.check_velocity(payment_method.token)

        has_customer = intent.customer_id is not None
        customer_is_new = False
        if has_customer and intent.customer is not None:
            age_seconds = (datetime.now(timezone.utc) - intent.customer.created_at).total_seconds()
            customer_is_new = age_seconds < 3600

        billing_country_mismatch = bool(
            billing_country and intent.merchant and billing_country.upper() != intent.merchant.country.upper()
        )

        score, requires_review = self.fraud_service.assess_and_maybe_flag(
            payment_intent_id=intent.id,
            merchant_id=merchant_id,
            amount_minor=intent.amount_minor,
            has_customer=has_customer,
            customer_is_new=customer_is_new,
            velocity_exceeded=velocity_exceeded,
            billing_country_mismatch=billing_country_mismatch,
            device_fingerprint=device_fingerprint,
            ip_address=ip_address,
        )

        intent = self.repo.update_status(intent, PaymentIntentStatus.PROCESSING, payment_method_id=payment_method.id)

        if requires_review:
            # Held for manual review — do NOT call the processor. An admin resolves this via
            # the fraud case decision endpoint, which calls _finalize_authorization below.
            return intent

        return self._finalize_authorization(intent, payment_method, merchant_id)

    def _finalize_authorization(self, intent, payment_method, merchant_id: uuid.UUID):
        """
        The actual authorize call + outcome handling — factored out so a fraud case
        approval (resolved later, possibly by an admin) can trigger the exact same
        path a normal, low-risk payment would have taken immediately.
        """
        result = self.processor.authorize(
            amount_minor=intent.amount_minor,
            currency=intent.currency,
            payment_method_token=payment_method.token,
        )

        event_payload = {
            "payment_intent_id": str(intent.id),
            "amount_minor": intent.amount_minor,
            "currency": intent.currency,
        }

        merchant_email = intent.merchant.business_email if intent.merchant else None

        if result.outcome == AuthorizationOutcome.APPROVED:
            intent = self.repo.update_status(intent, PaymentIntentStatus.SUCCEEDED)
            self.ledger_service.record_successful_payment(
                merchant_id=merchant_id,
                payment_intent_id=intent.id,
                amount_minor=intent.amount_minor,
                currency=intent.currency,
            )
            self.webhook_service.emit_event(merchant_id, "payment_intent.succeeded", event_payload)

            recipient = intent.customer.email if intent.customer_id and intent.customer and intent.customer.email else merchant_email
            if recipient:
                subject, body = build_payment_receipt(intent.amount_minor, intent.currency, intent.description)
                self.notification_service.send_notification(
                    merchant_id=merchant_id,
                    notification_type=NotificationType.PAYMENT_RECEIPT,
                    recipient_email=recipient,
                    subject=subject,
                    body=body,
                    customer_id=intent.customer_id,
                )
        elif result.outcome == AuthorizationOutcome.DECLINED:
            intent = self.repo.update_status(intent, PaymentIntentStatus.DECLINED, failure_reason=result.failure_reason)
            event_payload["failure_reason"] = result.failure_reason
            self.webhook_service.emit_event(merchant_id, "payment_intent.declined", event_payload)

            recipient = intent.customer.email if intent.customer_id and intent.customer and intent.customer.email else merchant_email
            if recipient:
                subject, body = build_payment_declined(intent.amount_minor, intent.currency, result.failure_reason)
                self.notification_service.send_notification(
                    merchant_id=merchant_id,
                    notification_type=NotificationType.PAYMENT_DECLINED,
                    recipient_email=recipient,
                    subject=subject,
                    body=body,
                    customer_id=intent.customer_id,
                )
        else:  # TIMEOUT
            intent = self.repo.update_status(intent, PaymentIntentStatus.PROCESSING, failure_reason=result.failure_reason)

        return intent

    def continue_after_fraud_review(self, merchant_id: uuid.UUID, intent_id: uuid.UUID, approved: bool):
        """Called by the fraud case resolution endpoint once an admin makes a decision."""
        intent = self.get_intent(merchant_id, intent_id)

        if not approved:
            return self.repo.update_status(intent, PaymentIntentStatus.DECLINED, failure_reason="manual_review_rejected")

        payment_method = self.repo.get_payment_method(merchant_id, intent.payment_method_id)
        return self._finalize_authorization(intent, payment_method, merchant_id)