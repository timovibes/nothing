"""
request/response schemas for blacklist entries, risk assessments, and fraud case review.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.fraud import FraudCaseStatus


class BlacklistCardRequest(BaseModel):
    card_fingerprint: str = Field(min_length=1, max_length=32)
    reason: str | None = None


class BlacklistIPRequest(BaseModel):
    ip_address: str = Field(min_length=1, max_length=45)
    reason: str | None = None


class RiskAssessmentResponse(BaseModel):
    id: uuid.UUID
    payment_intent_id: uuid.UUID
    score: int
    reasons: list[str]
    device_fingerprint: str | None
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class FraudCaseResponse(BaseModel):
    id: uuid.UUID
    payment_intent_id: uuid.UUID
    merchant_id: uuid.UUID
    risk_score: int
    status: FraudCaseStatus
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class FraudCaseDecisionRequest(BaseModel):
    approved: bool