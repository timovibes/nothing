"""
business logic for settings/flags/maintenance windows, report generation
(synchronous CSV/PDF export + summary aggregation), and merchant KYC verification.
"""

import csv
import os
import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.repositories.admin_repository import AdminRepository
from app.repositories.merchant_repository import MerchantRepository
from app.models.merchant import KycStatus
from app.models.admin import ReportStatus, ReportFormat, ReportExport
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
    REPORT_COLUMNS = ["id", "merchant_id", "amount_minor", "currency", "status", "created_at"]

    def _payment_rows(self) -> list[list[str]]:
        intents = self.db.query(PaymentIntent).order_by(PaymentIntent.created_at.desc()).all()
        return [
            [
                str(intent.id),
                str(intent.merchant_id),
                str(intent.amount_minor),
                intent.currency,
                intent.status.value,
                intent.created_at.isoformat(),
            ]
            for intent in intents
        ]

    def _write_csv(self, file_path: str, rows: list[list[str]]) -> None:
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.REPORT_COLUMNS)
            writer.writerows(rows)

    def _write_pdf(self, file_path: str, rows: list[list[str]]) -> None:
        doc = SimpleDocTemplate(file_path, pagesize=letter)
        table_data = [self.REPORT_COLUMNS] + rows
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.black),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        doc.build([table])

    def generate_report(self, requested_by: uuid.UUID, format: ReportFormat) -> ReportExport:
        report = self.repo.create_report(requested_by, "payments", format)

        try:
            os.makedirs(REPORTS_DIR, exist_ok=True)
            extension = "csv" if format == ReportFormat.CSV else "pdf"
            file_path = os.path.join(REPORTS_DIR, f"{report.id}.{extension}")

            rows = self._payment_rows()
            if format == ReportFormat.CSV:
                self._write_csv(file_path, rows)
            else:
                self._write_pdf(file_path, rows)

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

    def get_payments_summary(self, days: int = 30) -> dict:
        """
        Platform-wide (not merchant-scoped) aggregation for the admin reports page's charts.
        Sums amount_minor across all currencies with no FX conversion — a real multi-currency
        platform would need to convert to a common currency before summing; this is a known
        simplification worth flagging on the frontend rather than presenting as a real total.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        daily_rows = (
            self.db.query(
                func.date_trunc("day", PaymentIntent.created_at).label("day"),
                func.sum(PaymentIntent.amount_minor).label("total"),
                func.count(PaymentIntent.id).label("count"),
            )
            .filter(PaymentIntent.created_at >= cutoff)
            .group_by("day")
            .order_by("day")
            .all()
        )
        daily_revenue = [
            {"date": row.day.date().isoformat(), "amount_minor": int(row.total or 0), "count": row.count}
            for row in daily_rows
        ]

        status_rows = (
            self.db.query(PaymentIntent.status, func.count(PaymentIntent.id).label("count"))
            .filter(PaymentIntent.created_at >= cutoff)
            .group_by(PaymentIntent.status)
            .all()
        )
        status_breakdown = [{"status": row.status.value, "count": row.count} for row in status_rows]

        return {"daily_revenue": daily_revenue, "status_breakdown": status_breakdown}