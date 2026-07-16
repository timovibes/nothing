"""
the core webhook logic — registering endpoints, fanning an event out to every subscribed
endpoint as a delivery, HMAC-signing and sending each attempt, and scheduling retries on
failure using the compressed backoff schedule.
"""

import hashlib
import hmac
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.webhook import WebhookDeliveryStatus
from app.repositories.webhook_repository import WebhookRepository
from app.schemas.webhook import WebhookEndpointCreateRequest

# Compressed backoff schedule for local testing: 10s, 1min, 5min, 30min, then exhausted.
RETRY_SCHEDULE_SECONDS = [10, 60, 300, 1800]
DELIVERY_TIMEOUT_SECONDS = 5.0


class WebhookService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = WebhookRepository(db)

    def register_endpoint(self, merchant_id: uuid.UUID, payload: WebhookEndpointCreateRequest):
        signing_secret = "whsec_" + secrets.token_urlsafe(32)
        return self.repo.create_endpoint(
            merchant_id=merchant_id,
            url=str(payload.url),
            signing_secret=signing_secret,
            subscribed_events=payload.subscribed_events,
        )

    def list_endpoints(self, merchant_id: uuid.UUID):
        return self.repo.list_endpoints_for_merchant(merchant_id)

    def list_deliveries(self, merchant_id: uuid.UUID):
        return self.repo.list_deliveries_for_merchant(merchant_id)

    def emit_event(self, merchant_id: uuid.UUID, event_type: str, payload: dict) -> uuid.UUID:
        """
        Called from other services (payments, refunds, settlements) the moment something
        webhook-worthy happens. Creates the event record and one pending delivery per
        subscribed endpoint. Actual HTTP sending happens separately (via Celery task),
        so a slow/down merchant endpoint never blocks the request that triggered this.
        """
        event = self.repo.create_event(merchant_id, event_type, payload)

        endpoints = self.repo.list_active_endpoints_for_event(merchant_id, event_type)
        delivery_ids = []
        for endpoint in endpoints:
            delivery = self.repo.create_delivery(event.id, endpoint.id)
            delivery_ids.append(delivery.id)

        self.db.commit()
        return delivery_ids

    def _sign_payload(self, secret: str, raw_body: str) -> str:
        return hmac.new(secret.encode(), raw_body.encode(), hashlib.sha256).hexdigest()

    def attempt_delivery(self, delivery_id: uuid.UUID) -> WebhookDeliveryStatus:
        """
        Performs one actual HTTP delivery attempt: signs the payload, POSTs it,
        logs the raw request/response, and schedules the next retry on failure
        using RETRY_SCHEDULE_SECONDS. Marks EXHAUSTED once all retries are used.
        """
        delivery = self.repo.get_delivery(delivery_id)
        if delivery is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook delivery not found")

        event = delivery.webhook_event
        endpoint = delivery.webhook_endpoint

        body_dict = {
            "id": str(event.id),
            "type": event.event_type,
            "created_at": event.created_at.isoformat(),
            "data": event.payload,
        }
        raw_body = json.dumps(body_dict, default=str)
        signature = self._sign_payload(endpoint.signing_secret, raw_body)

        response_status_code = None
        response_body = None
        error_message = None
        succeeded = False

        try:
            with httpx.Client(timeout=DELIVERY_TIMEOUT_SECONDS) as client:
                response = client.post(
                    endpoint.url,
                    content=raw_body,
                    headers={
                        "Content-Type": "application/json",
                        "X-PayFlow-Signature": signature,
                        "X-PayFlow-Event-Type": event.event_type,
                    },
                )
            response_status_code = response.status_code
            response_body = response.text[:2000]
            succeeded = 200 <= response.status_code < 300
        except httpx.RequestError as e:
            error_message = str(e)[:1000]

        self.repo.create_log(
            webhook_delivery_id=delivery.id,
            request_body=raw_body,
            response_status_code=response_status_code,
            response_body=response_body,
            error_message=error_message,
        )

        if succeeded:
            self.repo.update_delivery_result(
                delivery,
                status=WebhookDeliveryStatus.SUCCEEDED,
                response_status_code=response_status_code,
                next_retry_at=None,
            )
            self.db.commit()
            return WebhookDeliveryStatus.SUCCEEDED

        # Failed — figure out if there's another retry left
        attempt_index = delivery.attempt_count  # 0-based: this failed attempt is attempt_index+1
        if attempt_index < len(RETRY_SCHEDULE_SECONDS):
            delay_seconds = RETRY_SCHEDULE_SECONDS[attempt_index]
            next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
            self.repo.update_delivery_result(
                delivery,
                status=WebhookDeliveryStatus.FAILED,
                response_status_code=response_status_code,
                next_retry_at=next_retry_at,
            )
            self.db.commit()
            return WebhookDeliveryStatus.FAILED
        else:
            self.repo.update_delivery_result(
                delivery,
                status=WebhookDeliveryStatus.EXHAUSTED,
                response_status_code=response_status_code,
                next_retry_at=None,
            )
            self.db.commit()
            return WebhookDeliveryStatus.EXHAUSTED

    def process_due_deliveries(self) -> list[uuid.UUID]:
        due = self.repo.get_due_deliveries()
        processed = []
        for delivery in due:
            self.attempt_delivery(delivery.id)
            processed.append(delivery.id)
        return processed