"""
the four Admin module tables — global settings, feature flags, maintenance windows, and
async report export tracking.
"""

import enum
import uuid

from sqlalchemy import Column, String, DateTime, Boolean, Enum, ForeignKey, func, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(JSONB, nullable=False)
    description = Column(String(500), nullable=True)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(100), nullable=False, index=True)
    # Nullable merchant_id: null = global flag, set = overrides the global value for one merchant
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=True, index=True)

    enabled = Column(Boolean, nullable=False, default=False)
    description = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class MaintenanceWindow(Base):
    __tablename__ = "maintenance_windows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    starts_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=False)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ReportExport(Base):
    __tablename__ = "report_exports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    report_type = Column(String(100), nullable=False)  # e.g. "payments_csv"
    status = Column(Enum(ReportStatus), nullable=False, default=ReportStatus.PENDING)
    file_path = Column(String(500), nullable=True)
    error_message = Column(String(1000), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)