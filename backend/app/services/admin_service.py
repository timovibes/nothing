"""
business logic for settings/flags/maintenance windows, report generation
(synchronous CSV export), and merchant KYC verification — the real replacement for our earlier
manual psql hack.
"""

import csv
import os
import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.admin_repository import AdminRepository
from app.repositories.merchant_repository import MerchantRepository
from app.models.merchant import KycStatus
from app.models.admin import ReportStatus, ReportExport
from app.models.payment import PaymentIntent

REPORTS_DIR = "storage/reports"


class AdminService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AdminRepository(db)
        self.merchant_repo = MerchantRepository(db)

    # --- Settings ---
    def set_setting(self, key: str, value: dict, description: str | None):
        return self.repo.upsert_setting(key, value, description)

    def list_settings(self):
        return self.repo.list_settings()

    # --- Feature flags ---
    def create_flag(self, key: str, merchant_id: uuid.UUID | None, enabled: bool, description: str | None):
        return self.repo.create_flag(key, merchant_id, enabled, description)

    def list_flags(self):
        return self.repo.list_flags()

    # --- Maintenance windows ---
    def create_window(self, title: str, description: str | None, starts_at: datetime, ends_at: datetime, created_by: uuid.UUID):
        if ends_at <= starts_at:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ends_at must be after starts_at")
        return self.repo.create_window(title, description, starts_at, ends_at, created_by)

    def list_status_page_windows(self):
        """Public — no auth required, matches the spec's 'shown in status page' behavior."""
        return self.repo.list_current_and_upcoming_windows()

    def list_all_windows(self):
        return self.repo.list_all_windows()

    # --- Merchant verification ---
    def verify_merchant(self, merchant_id: uuid.UUID, approved: bool, reason: str | None):
        merchant = self.merchant_repo.get_by_id(merchant_id)
        if merchant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")

        new_status = KycStatus.APPROVED if approved else KycStatus.REJECTED
        return self.merchant_repo.update_kyc_status(merchant, new_status, rejection_reason=None if approved else reason)

    # --- Report exports ---
    def generate_payments_report(self, requested_by: uuid.UUID) -> ReportExport:
        report = self.repo.create_report(requested_by, "payments_csv")

        try:
            os.makedirs(REPORTS_DIR, exist_ok=True)
            file_path = os.path.join(REPORTS_DIR, f"{report.id}.csv")

            intents = self.db.query(PaymentIntent).order_by(PaymentIntent.created_at.desc()).all()

            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["id", "merchant_id", "amount_minor", "currency", "status", "created_at"])
                for intent in intents:
                    writer.writerow([
                        str(intent.id),
                        str(intent.merchant_id),
                        intent.amount_minor,
                        intent.currency,
                        intent.status.value,
                        intent.created_at.isoformat(),
                    ])

            return self.repo.update_report_status(report, ReportStatus.COMPLETED, file_path=file_path)
        except Exception as e:
            return self.repo.update_report_status(report, ReportStatus.FAILED, error_message=str(e)[:1000])

    def get_report(self, report_id: uuid.UUID):
        report = self.repo.get_report(report_id)
        if report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
        return report

    def list_reports(self):
        return self.repo.list_reports()