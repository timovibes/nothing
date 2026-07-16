"""
merchant-facing blacklist management and risk visibility (secret API key), plus the
admin-only fraud case review queue and decision endpoint (dashboard JWT + admin role).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user, require_admin
from app.api.deps_apikey import get_merchant_from_api_key, AuthenticatedMerchant
from app.models.identity import User
from app.services.fraud_service import FraudService
from app.services.payment_service import PaymentService
from app.schemas.fraud import (
    BlacklistCardRequest,
    BlacklistIPRequest,
    RiskAssessmentResponse,
    FraudCaseResponse,
    FraudCaseDecisionRequest,
)

router = APIRouter(prefix="/api/v1/fraud", tags=["fraud"])


@router.post("/blacklist/cards", response_model=dict, status_code=status.HTTP_201_CREATED)
def blacklist_card(
    payload: BlacklistCardRequest,
    auth: AuthenticatedMerchant = Depends(get_merchant_from_api_key),
    db: Session = Depends(get_db),
):
    service = FraudService(db)
    entry = service.add_blacklisted_card(auth.merchant.id, payload.card_fingerprint, payload.reason)
    return {"id": str(entry.id), "card_fingerprint": entry.card_fingerprint}


@router.post("/blacklist/ips", response_model=dict, status_code=status.HTTP_201_CREATED)
def blacklist_ip(
    payload: BlacklistIPRequest,
    auth: AuthenticatedMerchant = Depends(get_merchant_from_api_key),
    db: Session = Depends(get_db),
):
    service = FraudService(db)
    entry = service.add_blacklisted_ip(auth.merchant.id, payload.ip_address, payload.reason)
    return {"id": str(entry.id), "ip_address": entry.ip_address}


@router.get("/risk-assessments", response_model=list[RiskAssessmentResponse])
def list_risk_assessments(
    auth: AuthenticatedMerchant = Depends(get_merchant_from_api_key),
    db: Session = Depends(get_db),
):
    service = FraudService(db)
    return service.list_risk_assessments(auth.merchant.id)


# --- Admin-only review queue ---

@router.get("/cases/pending", response_model=list[FraudCaseResponse], tags=["fraud-admin"])
def list_pending_cases(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    service = FraudService(db)
    return service.list_pending_fraud_cases()


@router.post("/cases/{case_id}/decide", response_model=FraudCaseResponse, tags=["fraud-admin"])
def decide_fraud_case(
    case_id: uuid.UUID,
    payload: FraudCaseDecisionRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    fraud_service = FraudService(db)
    case = fraud_service.get_fraud_case(case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fraud case not found")

    updated_case = fraud_service.resolve_fraud_case(case_id, payload.approved, admin.id)

    # Now actually continue (or decline) the held payment intent based on this decision
    payment_service = PaymentService(db)
    payment_service.continue_after_fraud_review(case.merchant_id, case.payment_intent_id, payload.approved)

    return updated_case