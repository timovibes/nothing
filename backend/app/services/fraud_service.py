"""
the actual fraud logic — hard blacklist gate, Redis-backed velocity counter, rules-based
risk scoring, and fraud case resolution that hands an approved case back to the Payment
Engine to continue processing.
"""

import hashlib
import uuid

from app.core.redis import redis_client
from app.repositories.fraud_repository import FraudRepository
from app.models.fraud import FraudCaseStatus

# Velocity: max attempts per card within the window, before flagging as suspicious
VELOCITY_MAX_ATTEMPTS = 3
VELOCITY_WINDOW_SECONDS = 600  # 10 minutes

# Risk scoring thresholds
RISK_REVIEW_THRESHOLD = 50
HIGH_VALUE_AMOUNT_MINOR = 2_000_000  # KES 20,000.00 — easy to hit deliberately in testing
NEW_CUSTOMER_WINDOW_SECONDS = 3600  # under 1 hour old counts as "new"


class FraudService:
    def __init__(self, db):
        self.db = db
        self.repo = FraudRepository(db)

    def card_fingerprint(self, card_last4: str, exp_month: int, exp_year: int) -> str:
        raw = f"{card_last4}-{exp_month}-{exp_year}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def check_blacklists(self, merchant_id: uuid.UUID, card_fingerprint: str, ip_address: str | None) -> str | None:
        """Hard gate — returns a block reason string if blocked, None if clear. Runs BEFORE authorization."""
        if self.repo.is_card_blacklisted(merchant_id, card_fingerprint):
            return "card_blacklisted"
        if ip_address and self.repo.is_ip_blacklisted(merchant_id, ip_address):
            return "ip_blacklisted"
        return None

    def check_velocity(self, card_token: str) -> bool:
        """
        Returns True if this card has exceeded the allowed attempt count within the window.
        Uses a simple Redis INCR + EXPIRE counter — the standard velocity-check pattern.
        """
        key = f"fraud:velocity:card:{card_token}"
        current_count = redis_client.incr(key)
        if current_count == 1:
            redis_client.expire(key, VELOCITY_WINDOW_SECONDS)
        return current_count > VELOCITY_MAX_ATTEMPTS

    def calculate_risk_score(
        self,
        amount_minor: int,
        has_customer: bool,
        customer_is_new: bool,
        velocity_exceeded: bool,
        billing_country_mismatch: bool,
    ) -> tuple[int, list[str]]:
        score = 0
        reasons = []

        is_high_value = amount_minor >= HIGH_VALUE_AMOUNT_MINOR

        if is_high_value:
            score += 30
            reasons.append("high_value_amount")

        if not has_customer:
            score += 20
            reasons.append("guest_checkout_no_customer_on_file")

        if customer_is_new and is_high_value:
            score += 25
            reasons.append("new_customer_with_high_value_payment")

        if velocity_exceeded:
            score += 40
            reasons.append("velocity_threshold_exceeded")

        if billing_country_mismatch:
            score += 15
            reasons.append("billing_country_mismatch")

        return min(score, 100), reasons

    def assess_and_maybe_flag(
        self,
        payment_intent_id: uuid.UUID,
        merchant_id: uuid.UUID,
        amount_minor: int,
        has_customer: bool,
        customer_is_new: bool,
        velocity_exceeded: bool,
        billing_country_mismatch: bool,
        device_fingerprint: str | None,
        ip_address: str | None,
    ) -> tuple[int, bool]:
        """Returns (score, requires_manual_review). Always records the assessment regardless of outcome."""
        score, reasons = self.calculate_risk_score(
            amount_minor=amount_minor,
            has_customer=has_customer,
            customer_is_new=customer_is_new,
            velocity_exceeded=velocity_exceeded,
            billing_country_mismatch=billing_country_mismatch,
        )

        self.repo.create_risk_assessment(
            payment_intent_id=payment_intent_id,
            merchant_id=merchant_id,
            score=score,
            reasons=reasons,
            device_fingerprint=device_fingerprint,
            ip_address=ip_address,
        )

        requires_review = score >= RISK_REVIEW_THRESHOLD
        if requires_review:
            self.repo.create_fraud_case(payment_intent_id, merchant_id, score)

        self.db.commit()
        return score, requires_review

    def add_blacklisted_card(self, merchant_id: uuid.UUID, card_fingerprint: str, reason: str | None):
        return self.repo.add_blacklisted_card(merchant_id, card_fingerprint, reason)

    def add_blacklisted_ip(self, merchant_id: uuid.UUID, ip_address: str, reason: str | None):
        return self.repo.add_blacklisted_ip(merchant_id, ip_address, reason)

    def list_risk_assessments(self, merchant_id: uuid.UUID):
        return self.repo.list_assessments_for_merchant(merchant_id)

    def list_pending_fraud_cases(self):
        return self.repo.list_pending_cases()

    def get_fraud_case(self, case_id: uuid.UUID):
        return self.repo.get_fraud_case(case_id)

    def resolve_fraud_case(self, case_id: uuid.UUID, approved: bool, reviewed_by: uuid.UUID):
        case = self.repo.get_fraud_case(case_id)
        if case is None:
            return None
        status = FraudCaseStatus.APPROVED if approved else FraudCaseStatus.REJECTED
        return self.repo.resolve_case(case, status, reviewed_by)