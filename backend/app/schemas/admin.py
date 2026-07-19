"""
request/response schemas for settings, feature flags, maintenance windows, merchant
verification, and report exports.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.admin import ReportStatus


class SystemSettingRequest(BaseModel):
    key: str
    value: dict
    description: str | None = None


class SystemSettingResponse(BaseModel):
    id: uuid.UUID
    key: str
    value: dict
    description: str | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class FeatureFlagRequest(BaseModel):
    key: str
    merchant_id: uuid.UUID | None = None
    enabled: bool
    description: str | None = None


class FeatureFlagResponse(BaseModel):
    id: uuid.UUID
    key: str
    merchant_id: uuid.UUID | None
    enabled: bool
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MaintenanceWindowRequest(BaseModel):
    title: str
    description: str | None = None
    starts_at: datetime
    ends_at: datetime


class MaintenanceWindowResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    starts_at: datetime
    ends_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class MerchantVerifyRequest(BaseModel):
    approved: bool
    reason: str | None = None


class ReportExportResponse(BaseModel):
    id: uuid.UUID
    report_type: str
    status: ReportStatus
    file_path: str | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}