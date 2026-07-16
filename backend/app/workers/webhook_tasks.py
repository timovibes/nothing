"""
Celery task wrappers — one delivers a single webhook attempt immediately
(fired the moment an event is emitted), another sweeps all due retries on a schedule.
"""

import uuid

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.webhook_service import WebhookService


@celery_app.task(name="app.workers.webhook_tasks.deliver_webhook_task")
def deliver_webhook_task(delivery_id: str):
    db = SessionLocal()
    try:
        service = WebhookService(db)
        result = service.attempt_delivery(uuid.UUID(delivery_id))
        return {"delivery_id": delivery_id, "status": result.value}
    finally:
        db.close()


@celery_app.task(name="app.workers.webhook_tasks.process_due_webhook_deliveries_task")
def process_due_webhook_deliveries_task():
    db = SessionLocal()
    try:
        service = WebhookService(db)
        processed = service.process_due_deliveries()
        return {"processed_count": len(processed)}
    finally:
        db.close()