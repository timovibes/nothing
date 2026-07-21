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

class WebhookEndpointDashboardResponse(BaseModel):
    id: uuid.UUID
    url: str
    masked_secret: str
    subscribed_events: list[str]
    is_active: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_endpoint(cls, endpoint) -> "WebhookEndpointDashboardResponse":
        secret = endpoint.signing_secret
        masked = secret[:10] + "…" + secret[-4:] if len(secret) > 14 else "whsec_••••"
        return cls(
            id=endpoint.id,
            url=endpoint.url,
            masked_secret=masked,
            subscribed_events=endpoint.subscribed_events,
            is_active=endpoint.is_active,
            created_at=endpoint.created_at,
        )