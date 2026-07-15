"""
request/response schemas for creating a merchant, viewing merchant details, and
displaying (never fully re-exposing) API keys
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.merchant import KycStatus, ApiKeyType


class MerchantCreateRequest(BaseModel):
    business_name: str = Field(min_length=1, max_length=255)
    business_email: EmailStr
    country: str = Field(default="KE", min_length=2, max_length=2)
    default_currency: str = Field(default="KES", min_length=3, max_length=3)


class MerchantResponse(BaseModel):
    id: uuid.UUID
    business_name: str
    business_email: EmailStr
    country: str
    default_currency: str
    kyc_status: KycStatus
    kyc_rejection_reason: str | None
    settlement_bank_name: str | None
    settlement_account_number: str | None
    settlement_account_name: str | None
    is_live_mode_enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SettlementDetailsRequest(BaseModel):
    settlement_bank_name: str = Field(min_length=1, max_length=255)
    settlement_account_number: str = Field(min_length=1, max_length=64)
    settlement_account_name: str = Field(min_length=1, max_length=255)


class ApiKeyCreatedResponse(BaseModel):
    id: uuid.UUID
    key_type: ApiKeyType
    display_prefix: str
    raw_key: str  # shown exactly once, at creation time only
    created_at: datetime


class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    key_type: ApiKeyType
    display_prefix: str
    is_active: bool
    created_at: datetime
    revoked_at: datetime | None

    model_config = {"from_attributes": True}