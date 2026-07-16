"""
Celery application configuration — uses Memurai/Redis as both broker and result backend,
with a beat schedule for the daily sweep and hourly payout-processing jobs.
"""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "payflow",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.settlement_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    "sweep-merchant-balances-daily": {
        "task": "app.workers.settlement_tasks.sweep_merchant_balances_task",
        "schedule": crontab(hour=2, minute=0),  # 02:00 UTC daily
    },
    "process-due-payouts-hourly": {
        "task": "app.workers.settlement_tasks.process_due_payouts_task",
        "schedule": crontab(minute=0),  # every hour, on the hour
    },
}