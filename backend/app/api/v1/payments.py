"""
HTTP routes for tokenizing cards and creating/confirming/listing payment intents. All
authenticated with the merchant's secret API key, not the dashboard JWT.
"""

import uuid

from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps_apikey import get_merchant_from_api_key, AuthenticatedMerchant
from app.services.payment_service import PaymentService
from app.schemas.payment import (
    TokenizeCardRequest,
    PaymentMethodResponse,
    PaymentIntentCreateRequest,
    PaymentIntentConfirmRequest,
    PaymentIntentResponse,
)


router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


@router.post("/payment-methods", response_model=PaymentMethodResponse, status_code=status.HTTP_201_CREATED)
def tokenize_card(
    payload: TokenizeCardRequest,
    auth: AuthenticatedMerchant = Depends(get_merchant_from_api_key),
    db: Session = Depends(get_db),
):
    service = PaymentService(db)
    return service.tokenize_card(auth.merchant.id, payload)


@router.post("/payment-intents", response_model=PaymentIntentResponse, status_code=status.HTTP_201_CREATED)
def create_payment_intent(
    payload: PaymentIntentCreateRequest,
    auth: AuthenticatedMerchant = Depends(get_merchant_from_api_key),
    db: Session = Depends(get_db),
):
    service = PaymentService(db)
    return service.create_intent(auth.merchant.id, auth.is_live_mode, payload)


@router.get("/payment-intents/{intent_id}", response_model=PaymentIntentResponse)
def get_payment_intent(
    intent_id: uuid.UUID,
    auth: AuthenticatedMerchant = Depends(get_merchant_from_api_key),
    db: Session = Depends(get_db),
):
    service = PaymentService(db)
    return service.get_intent(auth.merchant.id, intent_id)


@router.get("/payment-intents", response_model=list[PaymentIntentResponse])
def list_payment_intents(
    auth: AuthenticatedMerchant = Depends(get_merchant_from_api_key),
    db: Session = Depends(get_db),
):
    service = PaymentService(db)
    return service.list_intents(auth.merchant.id)


@router.post("/payment-intents/{intent_id}/confirm", response_model=PaymentIntentResponse)
def confirm_payment_intent(
    intent_id: uuid.UUID,
    payload: PaymentIntentConfirmRequest,
    request: Request,
    auth: AuthenticatedMerchant = Depends(get_merchant_from_api_key),
    db: Session = Depends(get_db),
):
    service = PaymentService(db)
    client_ip = request.client.host if request.client else None
    return service.confirm_intent(
        auth.merchant.id,
        intent_id,
        payload.payment_method_id,
        device_fingerprint=payload.device_fingerprint,
        billing_country=payload.billing_country,
        ip_address=client_ip,
    )