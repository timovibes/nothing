"""
Public-facing checkout endpoints — the ONLY payment routes safe to call from a customer's
browser. Authenticated with the merchant's publishable (pk_) key plus a per-intent
client_secret, never the secret (sk_) key. This is what the hosted Customer Checkout page
(design doc §4.1, §9.2) calls to tokenize a card and confirm a specific payment intent.
"""

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps_apikey import get_merchant_from_publishable_key, AuthenticatedMerchant
from app.services.payment_service import PaymentService
from app.schemas.payment import (
    TokenizeCardRequest,
    PaymentMethodResponse,
    PaymentIntentConfirmRequest,
    PaymentIntentResponse,
    PaymentIntentCheckoutResponse,
)

router = APIRouter(prefix="/api/v1/checkout", tags=["checkout"])


@router.get("/payment-intents/{intent_id}", response_model=PaymentIntentCheckoutResponse)
def get_checkout_intent(
    intent_id: uuid.UUID,
    client_secret: str,
    auth: AuthenticatedMerchant = Depends(get_merchant_from_publishable_key),
    db: Session = Depends(get_db),
):
    """Called when the Checkout page first loads, to render the amount/description."""
    service = PaymentService(db)
    return service.get_intent_for_checkout(intent_id, client_secret, auth.merchant.id)


@router.post("/payment-methods", response_model=PaymentMethodResponse, status_code=201)
def checkout_tokenize_card(
    payload: TokenizeCardRequest,
    auth: AuthenticatedMerchant = Depends(get_merchant_from_publishable_key),
    db: Session = Depends(get_db),
):
    """Card tokenization doesn't touch a specific intent, so pk_ auth alone is enough here —
    same as real Stripe, where Elements can tokenize before an intent is even confirmed."""
    service = PaymentService(db)
    return service.tokenize_card(auth.merchant.id, payload)


@router.post("/payment-intents/{intent_id}/confirm", response_model=PaymentIntentResponse)
def checkout_confirm_intent(
    intent_id: uuid.UUID,
    client_secret: str,
    payload: PaymentIntentConfirmRequest,
    request: Request,
    auth: AuthenticatedMerchant = Depends(get_merchant_from_publishable_key),
    db: Session = Depends(get_db),
):
    service = PaymentService(db)
    # Verifies the intent belongs to this merchant AND the secret matches — 404s otherwise
    service.get_intent_for_checkout(intent_id, client_secret, auth.merchant.id)

    client_ip = request.client.host if request.client else None
    return service.confirm_intent(
        auth.merchant.id,
        intent_id,
        payload.payment_method_id,
        device_fingerprint=payload.device_fingerprint,
        billing_country=payload.billing_country,
        ip_address=client_ip,
    )