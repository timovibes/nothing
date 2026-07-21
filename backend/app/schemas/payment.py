"""
request/response schemas for tokenizing a card, creating a payment intent, and
confirming (authorizing) it.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.payment import PaymentIntentStatus, CardBrand


class TokenizeCardRequest(BaseModel):
    card_number: str = Field(min_length=12, max_length=19)
    exp_month: int = Field(ge=1, le=12)
    exp_year: int = Field(ge=2024, le=2100)
    cvv: str = Field(min_length=3, max_length=4)

    @field_validator("card_number")
    @classmethod
    def digits_only(cls, v: str) -> str:
        cleaned = v.replace(" ", "").replace("-", "")
        if not cleaned.isdigit():
            raise ValueError("card_number must contain only digits")
        return cleaned


class PaymentMethodResponse(BaseModel):
    id: uuid.UUID
    card_brand: CardBrand
    card_last4: str
    card_exp_month: int
    card_exp_year: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentIntentCreateRequest(BaseModel):
    amount_minor: int = Field(gt=0, description="Amount in smallest currency unit, e.g. cents")
    currency: str = Field(min_length=3, max_length=3)
    customer_id: uuid.UUID | None = None
    description: str | None = Field(default=None, max_length=500)
    idempotency_key: str | None = Field(default=None, max_length=255)


class PaymentIntentConfirmRequest(BaseModel):
    payment_method_id: uuid.UUID
    device_fingerprint: str | None = None
    billing_country: str | None = None


class PaymentIntentResponse(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID | None
    amount_minor: int
    currency: str
    status: PaymentIntentStatus
    description: str | None
    failure_reason: str | None
    is_live_mode: str
    client_secret: str | None   # <-- add this. Safe here: only the merchant's own sk_-authenticated
                                # backend ever sees this response shape, never the browser directly.
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    model_config = {"from_attributes": True}

class PaymentIntentCheckoutResponse(BaseModel):
    """
    What the Checkout page is allowed to see about an intent — deliberately excludes
    merchant_id, idempotency_key, is_live_mode internals, etc.
    """
    id: uuid.UUID
    amount_minor: int
    currency: str
    description: str | None
    status: PaymentIntentStatus

    model_config = {"from_attributes": True}