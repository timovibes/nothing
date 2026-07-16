"""
request/response schemas for registering webhook endpoints and viewing delivery history.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, HttpUrl, Field

from app.models.webhook import WebhookDeliveryStatus


class WebhookEndpointCreateRequest(BaseModel):
    url: HttpUrl
    subscribed_events: list[str] = Field(
        default_factory=list,
        description="e.g. ['payment_intent.succeeded', 'payment_intent.refunded']. Empty = subscribe to all events.",
    )


class WebhookEndpointResponse(BaseModel):
    id: uuid.UUID
    url: str
    signing_secret: str
    subscribed_events: list[str]
    is_active: str
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookDeliveryResponse(BaseModel):
    id: uuid.UUID
    webhook_event_id: uuid.UUID
    webhook_endpoint_id: uuid.UUID
    status: WebhookDeliveryStatus
    attempt_count: int
    next_retry_at: datetime | None
    last_attempted_at: datetime | None
    last_response_status_code: int | None
    created_at: datetime

    model_config = {"from_attributes": True}