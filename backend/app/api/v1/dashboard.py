"""
JWT-authenticated read endpoints purpose-built for the browser dashboard — same underlying
services as the API-key routes, but resolving the merchant from the logged-in user's session
instead of a secret key.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.identity import User
from app.repositories.ledger_repository import LedgerRepository
from app.services.payment_service import PaymentService
from app.services.settlement_service import SettlementService
from app.schemas.payment import PaymentIntentResponse
from app.schemas.ledger import WalletBalanceResponse
from app.schemas.settlement import PayoutResponse
from app.services.refund_service import RefundService
from app.services.customer_service import CustomerService
from app.services.webhook_service import WebhookService
from app.schemas.refund import RefundResponse
from app.schemas.customer import CustomerResponse
from app.schemas.webhook import WebhookEndpointDashboardResponse, WebhookDeliveryResponse
from app.schemas.refund import RefundCreateRequest
from app.schemas.customer import CustomerCreateRequest
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


def _require_merchant_id(user: User) -> uuid.UUID:
    if user.merchant_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This user has no merchant account yet")
    return user.merchant_id


@router.get("/wallet-balance", response_model=list[WalletBalanceResponse])
def get_wallet_balance(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    merchant_id = _require_merchant_id(current_user)
    repo = LedgerRepository(db)
    wallet = repo.get_or_create_wallet(merchant_id, current_user.merchant.default_currency)
    db.commit()
    return [wallet]


@router.get("/payment-intents", response_model=list[PaymentIntentResponse])
def list_payment_intents(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    merchant_id = _require_merchant_id(current_user)
    service = PaymentService(db)
    return service.list_intents(merchant_id)


@router.get("/payouts", response_model=list[PayoutResponse])
def list_payouts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    merchant_id = _require_merchant_id(current_user)
    service = SettlementService(db)
    return service.list_payouts_for_merchant(merchant_id)

@router.get("/refunds", response_model=list[RefundResponse])
def list_refunds(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    merchant_id = _require_merchant_id(current_user)
    service = RefundService(db)
    return service.list_refunds_for_merchant(merchant_id)


@router.get("/customers", response_model=list[CustomerResponse])
def list_customers(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    merchant_id = _require_merchant_id(current_user)
    service = CustomerService(db)
    return service.list_customers(merchant_id)


@router.get("/webhook-endpoints", response_model=list[WebhookEndpointDashboardResponse])
def list_webhook_endpoints(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    merchant_id = _require_merchant_id(current_user)
    service = WebhookService(db)
    endpoints = service.list_endpoints(merchant_id)
    return [WebhookEndpointDashboardResponse.from_endpoint(e) for e in endpoints]


@router.get("/webhook-deliveries", response_model=list[WebhookDeliveryResponse])
def list_webhook_deliveries(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    merchant_id = _require_merchant_id(current_user)
    service = WebhookService(db)
    return service.list_deliveries(merchant_id)

@router.post("/payment-intents/{intent_id}/refund", response_model=RefundResponse, status_code=201)
def create_refund_from_dashboard(
    intent_id: uuid.UUID,
    payload: RefundCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    merchant_id = _require_merchant_id(current_user)
    service = RefundService(db)
    return service.create_refund(merchant_id, intent_id, payload)

@router.post("/customers", response_model=CustomerResponse, status_code=201)
def create_customer_from_dashboard(
    payload: CustomerCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    merchant_id = _require_merchant_id(current_user)
    service = CustomerService(db)
    return service.create_customer(merchant_id, payload)