"""
the actual Celery task wrappers that Celery Beat calls on schedule — each opens its own
DB session (Celery tasks run in separate worker processes, so they can't reuse FastAPI's
request-scoped session).
"""

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.settlement_service import SettlementService


@celery_app.task(name="app.workers.settlement_tasks.sweep_merchant_balances_task")
def sweep_merchant_balances_task():
    db = SessionLocal()
    try:
        service = SettlementService(db)
        results = service.sweep_all_merchant_balances()
        return {"swept_count": len(results)}
    finally:
        db.close()


@celery_app.task(name="app.workers.settlement_tasks.process_due_payouts_task")
def process_due_payouts_task():
    db = SessionLocal()
    try:
        service = SettlementService(db)
        paid_ids = service.process_due_payouts(ignore_date_check=False)
        return {"paid_count": len(paid_ids)}
    finally:
        db.close()