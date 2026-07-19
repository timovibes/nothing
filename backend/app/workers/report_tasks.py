"""
Celery task wrapper for report generation, for real deployments where a worker actually runs
(mirrors the sync/async pattern used in every earlier module).
"""

import uuid

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.admin_service import AdminService


@celery_app.task(name="app.workers.report_tasks.generate_payments_report_task")
def generate_payments_report_task(requested_by: str):
    db = SessionLocal()
    try:
        service = AdminService(db)
        report = service.generate_payments_report(uuid.UUID(requested_by))
        return {"report_id": str(report.id), "status": report.status.value}
    finally:
        db.close()