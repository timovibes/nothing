"""
Pydantic request/response schemas for register, login, token responses,
and the current-user payload.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.identity import UserRole


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    merchant_id: uuid.UUID | None
    is_active: bool
    is_email_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class OtpRequiredResponse(BaseModel):
    otp_required: bool = True
    otp_session_id: str


class VerifyOtpRequest(BaseModel):
    otp_session_id: str
    code: str = Field(min_length=6, max_length=6)

class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class StaffInviteRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)


class StaffMemberResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AcceptInviteRequest(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=128)

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)