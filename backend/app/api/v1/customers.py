"""
HTTP routes to create, view, and list a merchant's customers — authenticated with the secret
API key, same as payments (this is data the merchant's own backend manages, not their dashboard
login).
"""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps_apikey import get_merchant_from_api_key, AuthenticatedMerchant
from app.services.customer_service import CustomerService
from app.schemas.customer import CustomerCreateRequest, CustomerResponse

router = APIRouter(prefix="/api/v1/customers", tags=["customers"])


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    payload: CustomerCreateRequest,
    auth: AuthenticatedMerchant = Depends(get_merchant_from_api_key),
    db: Session = Depends(get_db),
):
    service = CustomerService(db)
    return service.create_customer(auth.merchant.id, payload)


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: uuid.UUID,
    auth: AuthenticatedMerchant = Depends(get_merchant_from_api_key),
    db: Session = Depends(get_db),
):
    service = CustomerService(db)
    return service.get_customer(auth.merchant.id, customer_id)


@router.get("", response_model=list[CustomerResponse])
def list_customers(
    auth: AuthenticatedMerchant = Depends(get_merchant_from_api_key),
    db: Session = Depends(get_db),
):
    service = CustomerService(db)
    return service.list_customers(auth.merchant.id)