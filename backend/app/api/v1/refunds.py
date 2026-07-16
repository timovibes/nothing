"""
HTTP routes to create a refund against a payment intent and list its refund
history — authenticated with the merchant's secret API key, same as payments.
"""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps_apikey import get_merchant_from_api_key, AuthenticatedMerchant
from app.services.refund_service import RefundService
from app.schemas.refund import RefundCreateRequest, RefundResponse

router = APIRouter(prefix="/api/v1/payments/payment-intents", tags=["refunds"])


@router.post("/{intent_id}/refunds", response_model=RefundResponse, status_code=status.HTTP_201_CREATED)
def create_refund(
    intent_id: uuid.UUID,
    payload: RefundCreateRequest,
    auth: AuthenticatedMerchant = Depends(get_merchant_from_api_key),
    db: Session = Depends(get_db),
):
    service = RefundService(db)
    return service.create_refund(auth.merchant.id, intent_id, payload)


@router.get("/{intent_id}/refunds", response_model=list[RefundResponse])
def list_refunds(
    intent_id: uuid.UUID,
    auth: AuthenticatedMerchant = Depends(get_merchant_from_api_key),
    db: Session = Depends(get_db),
):
    service = RefundService(db)
    return service.list_refunds_for_intent(auth.merchant.id, intent_id)