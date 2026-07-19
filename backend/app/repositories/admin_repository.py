#  direct database queries for all four Admin tables.
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.admin import SystemSetting, FeatureFlag, MaintenanceWindow, ReportExport, ReportStatus


class AdminRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- System settings ---
    def upsert_setting(self, key: str, value: dict, description: str | None) -> SystemSetting:
        setting = self.db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if setting is None:
            setting = SystemSetting(key=key, value=value, description=description)
        else:
            setting.value = value
            setting.description = description
        self.db.add(setting)
        self.db.commit()
        self.db.refresh(setting)
        return setting

    def list_settings(self) -> list[SystemSetting]:
        return self.db.query(SystemSetting).order_by(SystemSetting.key.asc()).all()

    def get_setting(self, key: str) -> SystemSetting | None:
        return self.db.query(SystemSetting).filter(SystemSetting.key == key).first()

    # --- Feature flags ---
    def create_flag(self, key: str, merchant_id: uuid.UUID | None, enabled: bool, description: str | None) -> FeatureFlag:
        flag = FeatureFlag(key=key, merchant_id=merchant_id, enabled=enabled, description=description)
        self.db.add(flag)
        self.db.commit()
        self.db.refresh(flag)
        return flag

    def list_flags(self) -> list[FeatureFlag]:
        return self.db.query(FeatureFlag).order_by(FeatureFlag.key.asc()).all()

    def is_enabled(self, key: str, merchant_id: uuid.UUID | None) -> bool:
        if merchant_id:
            merchant_flag = (
                self.db.query(FeatureFlag).filter(FeatureFlag.key == key, FeatureFlag.merchant_id == merchant_id).first()
            )
            if merchant_flag:
                return merchant_flag.enabled
        global_flag = self.db.query(FeatureFlag).filter(FeatureFlag.key == key, FeatureFlag.merchant_id.is_(None)).first()
        return global_flag.enabled if global_flag else False

    # --- Maintenance windows ---
    def create_window(self, title: str, description: str | None, starts_at, ends_at, created_by: uuid.UUID) -> MaintenanceWindow:
        window = MaintenanceWindow(title=title, description=description, starts_at=starts_at, ends_at=ends_at, created_by=created_by)
        self.db.add(window)
        self.db.commit()
        self.db.refresh(window)
        return window

    def list_current_and_upcoming_windows(self) -> list[MaintenanceWindow]:
        now = datetime.now(timezone.utc)
        return (
            self.db.query(MaintenanceWindow)
            .filter(MaintenanceWindow.ends_at >= now)
            .order_by(MaintenanceWindow.starts_at.asc())
            .all()
        )

    def list_all_windows(self) -> list[MaintenanceWindow]:
        return self.db.query(MaintenanceWindow).order_by(MaintenanceWindow.starts_at.desc()).all()

    # --- Report exports ---
    def create_report(self, requested_by: uuid.UUID, report_type: str) -> ReportExport:
        report = ReportExport(requested_by=requested_by, report_type=report_type, status=ReportStatus.PENDING)
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def update_report_status(
        self, report: ReportExport, status: ReportStatus, file_path: str | None = None, error_message: str | None = None
    ) -> ReportExport:
        report.status = status
        report.file_path = file_path
        report.error_message = error_message
        if status in (ReportStatus.COMPLETED, ReportStatus.FAILED):
            report.completed_at = datetime.now(timezone.utc)
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_report(self, report_id: uuid.UUID) -> ReportExport | None:
        return self.db.query(ReportExport).filter(ReportExport.id == report_id).first()

    def list_reports(self) -> list[ReportExport]:
        return self.db.query(ReportExport).order_by(ReportExport.created_at.desc()).all()