# request/response schemas for creating and viewing refunds.

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.refund import RefundStatus


class RefundCreateRequest(BaseModel):
    amount_minor: int | None = Field(default=None, gt=0, description="Omit for a full refund of the remaining amount")
    reason: str | None = Field(default=None, max_length=500)


class RefundResponse(BaseModel):
    id: uuid.UUID
    payment_intent_id: uuid.UUID
    amount_minor: int
    currency: str
    status: RefundStatus
    reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}