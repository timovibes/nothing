# response schemas for viewing API logs, audit logs, and login sessions.

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.audit import ActorType


class ApiLogResponse(BaseModel):
    id: uuid.UUID
    method: str
    path: str
    status_code: int
    latency_ms: float
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    actor_type: ActorType
    actor_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: uuid.UUID | None
    request_body: dict | None
    status_code: int
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginSessionResponse(BaseModel):
    id: uuid.UUID
    email_attempted: str
    ip_address: str | None
    device: str | None
    success: bool
    created_at: datetime

    model_config = {"from_attributes": True}