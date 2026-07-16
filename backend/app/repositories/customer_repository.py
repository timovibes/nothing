"""
direct database queries for customers.
"""
import uuid

from sqlalchemy.orm import Session

from app.models.customer import Customer


class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, merchant_id: uuid.UUID, email: str | None, full_name: str | None, phone: str | None) -> Customer:
        customer = Customer(merchant_id=merchant_id, email=email, full_name=full_name, phone=phone)
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def get_by_id(self, merchant_id: uuid.UUID, customer_id: uuid.UUID) -> Customer | None:
        return (
            self.db.query(Customer)
            .filter(Customer.id == customer_id, Customer.merchant_id == merchant_id)
            .first()
        )

    def list_for_merchant(self, merchant_id: uuid.UUID) -> list[Customer]:
        return (
            self.db.query(Customer)
            .filter(Customer.merchant_id == merchant_id)
            .order_by(Customer.created_at.desc())
            .all()
        )