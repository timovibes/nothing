"""
 thin business logic layer for customer creation and lookup (deliberately simple — customers
 have no complex state machine, unlike payments).
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.customer_repository import CustomerRepository
from app.schemas.customer import CustomerCreateRequest


class CustomerService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CustomerRepository(db)

    def create_customer(self, merchant_id: uuid.UUID, payload: CustomerCreateRequest):
        return self.repo.create(
            merchant_id=merchant_id,
            email=payload.email,
            full_name=payload.full_name,
            phone=payload.phone,
        )

    def get_customer(self, merchant_id: uuid.UUID, customer_id: uuid.UUID):
        customer = self.repo.get_by_id(merchant_id, customer_id)
        if customer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        return customer

    def list_customers(self, merchant_id: uuid.UUID):
        return self.repo.list_for_merchant(merchant_id)