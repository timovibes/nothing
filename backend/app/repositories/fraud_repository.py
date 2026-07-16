#direct database queries for blacklist checks, risk assessments, and fraud case management.
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.fraud import BlacklistedCard, BlacklistedIP, RiskAssessment, FraudCase, FraudCaseStatus


class FraudRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- Blacklists ---
    def is_card_blacklisted(self, merchant_id: uuid.UUID, card_fingerprint: str) -> bool:
        return (
            self.db.query(BlacklistedCard)
            .filter(
                BlacklistedCard.card_fingerprint == card_fingerprint,
                (BlacklistedCard.merchant_id == merchant_id) | (BlacklistedCard.merchant_id.is_(None)),
            )
            .first()
            is not None
        )

    def is_ip_blacklisted(self, merchant_id: uuid.UUID, ip_address: str) -> bool:
        return (
            self.db.query(BlacklistedIP)
            .filter(
                BlacklistedIP.ip_address == ip_address,
                (BlacklistedIP.merchant_id == merchant_id) | (BlacklistedIP.merchant_id.is_(None)),
            )
            .first()
            is not None
        )

    def add_blacklisted_card(self, merchant_id: uuid.UUID, card_fingerprint: str, reason: str | None) -> BlacklistedCard:
        entry = BlacklistedCard(merchant_id=merchant_id, card_fingerprint=card_fingerprint, reason=reason)
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def add_blacklisted_ip(self, merchant_id: uuid.UUID, ip_address: str, reason: str | None) -> BlacklistedIP:
        entry = BlacklistedIP(merchant_id=merchant_id, ip_address=ip_address, reason=reason)
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    # --- Risk assessments ---
    def create_risk_assessment(
        self,
        payment_intent_id: uuid.UUID,
        merchant_id: uuid.UUID,
        score: int,
        reasons: list[str],
        device_fingerprint: str | None,
        ip_address: str | None,
    ) -> RiskAssessment:
        assessment = RiskAssessment(
            payment_intent_id=payment_intent_id,
            merchant_id=merchant_id,
            score=score,
            reasons=reasons,
            device_fingerprint=device_fingerprint,
            ip_address=ip_address,
        )
        self.db.add(assessment)
        self.db.flush()
        return assessment

    def list_assessments_for_merchant(self, merchant_id: uuid.UUID) -> list[RiskAssessment]:
        return (
            self.db.query(RiskAssessment)
            .filter(RiskAssessment.merchant_id == merchant_id)
            .order_by(RiskAssessment.created_at.desc())
            .all()
        )

    # --- Fraud cases ---
    def create_fraud_case(self, payment_intent_id: uuid.UUID, merchant_id: uuid.UUID, risk_score: int) -> FraudCase:
        case = FraudCase(payment_intent_id=payment_intent_id, merchant_id=merchant_id, risk_score=risk_score)
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)
        return case

    def get_fraud_case_by_intent(self, payment_intent_id: uuid.UUID) -> FraudCase | None:
        return self.db.query(FraudCase).filter(FraudCase.payment_intent_id == payment_intent_id).first()

    def get_fraud_case(self, case_id: uuid.UUID) -> FraudCase | None:
        return self.db.query(FraudCase).filter(FraudCase.id == case_id).first()

    def list_pending_cases(self) -> list[FraudCase]:
        return self.db.query(FraudCase).filter(FraudCase.status == FraudCaseStatus.PENDING).order_by(FraudCase.created_at.asc()).all()

    def resolve_case(self, case: FraudCase, status: FraudCaseStatus, reviewed_by: uuid.UUID) -> FraudCase:
        case.status = status
        case.reviewed_by = reviewed_by
        case.reviewed_at = datetime.now(timezone.utc)
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)
        return case