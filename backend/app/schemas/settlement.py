# response schema for viewing a merchant's payout history.

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.settlement import PayoutStatus


class PayoutResponse(BaseModel):
    id: uuid.UUID
    amount_minor: int
    currency: str
    status: PayoutStatus
    failure_reason: str | None
    initiated_at: datetime
    expected_arrival_at: datetime
    paid_at: datetime | None

    model_config = {"from_attributes": True}