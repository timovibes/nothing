#direct database queries for webhook endpoints, events, deliveries, and logs.
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.webhook import WebhookEndpoint, WebhookEvent, WebhookDelivery, WebhookLog, WebhookDeliveryStatus


class WebhookRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- Endpoints ---
    def create_endpoint(self, merchant_id: uuid.UUID, url: str, signing_secret: str, subscribed_events: list[str]) -> WebhookEndpoint:
        endpoint = WebhookEndpoint(
            merchant_id=merchant_id,
            url=url,
            signing_secret=signing_secret,
            subscribed_events=subscribed_events,
        )
        self.db.add(endpoint)
        self.db.commit()
        self.db.refresh(endpoint)
        return endpoint

    def list_active_endpoints_for_event(self, merchant_id: uuid.UUID, event_type: str) -> list[WebhookEndpoint]:
        endpoints = (
            self.db.query(WebhookEndpoint)
            .filter(WebhookEndpoint.merchant_id == merchant_id, WebhookEndpoint.is_active == "active")
            .all()
        )
        # Empty subscribed_events list means "subscribe to everything"
        return [e for e in endpoints if not e.subscribed_events or event_type in e.subscribed_events]

    def list_endpoints_for_merchant(self, merchant_id: uuid.UUID) -> list[WebhookEndpoint]:
        return self.db.query(WebhookEndpoint).filter(WebhookEndpoint.merchant_id == merchant_id).all()

    def get_endpoint(self, merchant_id: uuid.UUID, endpoint_id: uuid.UUID) -> WebhookEndpoint | None:
        return (
            self.db.query(WebhookEndpoint)
            .filter(WebhookEndpoint.id == endpoint_id, WebhookEndpoint.merchant_id == merchant_id)
            .first()
        )

    # --- Events ---
    def create_event(self, merchant_id: uuid.UUID, event_type: str, payload: dict) -> WebhookEvent:
        event = WebhookEvent(merchant_id=merchant_id, event_type=event_type, payload=payload)
        self.db.add(event)
        self.db.flush()
        return event

    # --- Deliveries ---
    def create_delivery(self, webhook_event_id: uuid.UUID, webhook_endpoint_id: uuid.UUID) -> WebhookDelivery:
        delivery = WebhookDelivery(
            webhook_event_id=webhook_event_id,
            webhook_endpoint_id=webhook_endpoint_id,
            status=WebhookDeliveryStatus.PENDING,
        )
        self.db.add(delivery)
        self.db.flush()
        return delivery

    def get_delivery(self, delivery_id: uuid.UUID) -> WebhookDelivery | None:
        return self.db.query(WebhookDelivery).filter(WebhookDelivery.id == delivery_id).first()

    def get_due_deliveries(self) -> list[WebhookDelivery]:
        return (
            self.db.query(WebhookDelivery)
            .filter(
                WebhookDelivery.status.in_([WebhookDeliveryStatus.PENDING, WebhookDeliveryStatus.FAILED]),
                (WebhookDelivery.next_retry_at.is_(None)) | (WebhookDelivery.next_retry_at <= datetime.now(timezone.utc)),
            )
            .all()
        )

    def update_delivery_result(
        self,
        delivery: WebhookDelivery,
        status: WebhookDeliveryStatus,
        response_status_code: int | None,
        next_retry_at: datetime | None,
    ) -> WebhookDelivery:
        delivery.status = status
        delivery.attempt_count += 1
        delivery.last_attempted_at = datetime.now(timezone.utc)
        delivery.last_response_status_code = response_status_code
        delivery.next_retry_at = next_retry_at
        self.db.add(delivery)
        return delivery

    def list_deliveries_for_merchant(self, merchant_id: uuid.UUID) -> list[WebhookDelivery]:
        return (
            self.db.query(WebhookDelivery)
            .join(WebhookEvent, WebhookDelivery.webhook_event_id == WebhookEvent.id)
            .filter(WebhookEvent.merchant_id == merchant_id)
            .order_by(WebhookDelivery.created_at.desc())
            .all()
        )

    # --- Logs ---
    def create_log(
        self,
        webhook_delivery_id: uuid.UUID,
        request_body: str,
        response_status_code: int | None,
        response_body: str | None,
        error_message: str | None,
    ) -> WebhookLog:
        log = WebhookLog(
            webhook_delivery_id=webhook_delivery_id,
            request_body=request_body,
            response_status_code=response_status_code,
            response_body=response_body,
            error_message=error_message,
        )
        self.db.add(log)
        return log