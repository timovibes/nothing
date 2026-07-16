# request/response schemas for creating and viewing customers.
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class CustomerCreateRequest(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)


class CustomerResponse(BaseModel):
    id: uuid.UUID
    email: str | None
    full_name: str | None
    phone: str | None
    created_at: datetime

    model_config = {"from_attributes": True}