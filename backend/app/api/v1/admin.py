"""
every Admin route, all gated behind the admin role — settings, feature flags, maintenance
windows (plus a public status-page view), merchant verification, and report generation/download.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import require_admin
from app.models.identity import User
from app.services.admin_service import AdminService
from app.services.merchant_service import MerchantService
from app.schemas.admin import (
    SystemSettingRequest,
    SystemSettingResponse,
    FeatureFlagRequest,
    FeatureFlagResponse,
    MaintenanceWindowRequest,
    MaintenanceWindowResponse,
    MerchantVerifyRequest,
    ReportExportResponse,
)
from app.schemas.merchant import MerchantResponse

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


# --- System settings ---
@router.put("/settings", response_model=SystemSettingResponse)
def upsert_setting(payload: SystemSettingRequest, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    service = AdminService(db)
    return service.set_setting(payload.key, payload.value, payload.description)


@router.get("/settings", response_model=list[SystemSettingResponse])
def list_settings(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    service = AdminService(db)
    return service.list_settings()


# --- Feature flags ---
@router.post("/feature-flags", response_model=FeatureFlagResponse, status_code=status.HTTP_201_CREATED)
def create_flag(payload: FeatureFlagRequest, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    service = AdminService(db)
    return service.create_flag(payload.key, payload.merchant_id, payload.enabled, payload.description)


@router.get("/feature-flags", response_model=list[FeatureFlagResponse])
def list_flags(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    service = AdminService(db)
    return service.list_flags()


# --- Maintenance windows ---
@router.post("/maintenance-windows", response_model=MaintenanceWindowResponse, status_code=status.HTTP_201_CREATED)
def create_window(payload: MaintenanceWindowRequest, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    service = AdminService(db)
    return service.create_window(payload.title, payload.description, payload.starts_at, payload.ends_at, admin.id)


@router.get("/maintenance-windows", response_model=list[MaintenanceWindowResponse])
def list_all_windows(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    service = AdminService(db)
    return service.list_all_windows()


# --- Merchant verification ---
@router.post("/merchants/{merchant_id}/verify", response_model=MerchantResponse)
def verify_merchant(
    merchant_id: uuid.UUID,
    payload: MerchantVerifyRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    return service.verify_merchant(merchant_id, payload.approved, payload.reason)


# --- Report exports ---
@router.post("/reports/payments-csv", response_model=ReportExportResponse, status_code=status.HTTP_201_CREATED)
def generate_payments_report(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    service = AdminService(db)
    return service.generate_payments_report(admin.id)


@router.get("/reports", response_model=list[ReportExportResponse])
def list_reports(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    service = AdminService(db)
    return service.list_reports()


@router.get("/reports/{report_id}/download")
def download_report(report_id: uuid.UUID, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    service = AdminService(db)
    report = service.get_report(report_id)
    if report.file_path is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Report has no file available")
    return FileResponse(report.file_path, filename=f"{report.report_type}_{report.id}.csv", media_type="text/csv")


# --- Public status page (no auth) ---
@router.get("/status-page/maintenance-windows", response_model=list[MaintenanceWindowResponse], tags=["public"])
def public_maintenance_windows(db: Session = Depends(get_db)):
    service = AdminService(db)
    return service.list_status_page_windows()