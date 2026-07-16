"""
HTTP routes to register a webhook endpoint, list a merchant's endpoints, and view delivery
history — authenticated with the secret API key.
"""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps_apikey import get_merchant_from_api_key, AuthenticatedMerchant
from app.services.webhook_service import WebhookService
from app.schemas.webhook import WebhookEndpointCreateRequest, WebhookEndpointResponse, WebhookDeliveryResponse

router = APIRouter(prefix="/api/v1/webhook-endpoints", tags=["webhooks"])


@router.post("", response_model=WebhookEndpointResponse, status_code=status.HTTP_201_CREATED)
def register_endpoint(
    payload: WebhookEndpointCreateRequest,
    auth: AuthenticatedMerchant = Depends(get_merchant_from_api_key),
    db: Session = Depends(get_db),
):
    service = WebhookService(db)
    return service.register_endpoint(auth.merchant.id, payload)


@router.get("", response_model=list[WebhookEndpointResponse])
def list_endpoints(
    auth: AuthenticatedMerchant = Depends(get_merchant_from_api_key),
    db: Session = Depends(get_db),
):
    service = WebhookService(db)
    return service.list_endpoints(auth.merchant.id)


@router.get("/deliveries", response_model=list[WebhookDeliveryResponse])
def list_deliveries(
    auth: AuthenticatedMerchant = Depends(get_merchant_from_api_key),
    db: Session = Depends(get_db),
):
    service = WebhookService(db)
    return service.list_deliveries(auth.merchant.id)


# --- TEST-ONLY ENDPOINT ---
# Forces the retry sweep to run immediately, instead of waiting for Celery Beat's 15-second schedule.
@router.post("/test/trigger-delivery-sweep", tags=["webhooks-test-only"])
def test_trigger_delivery_sweep(db: Session = Depends(get_db)):
    service = WebhookService(db)
    processed = service.process_due_deliveries()
    return {"processed_delivery_ids": processed}