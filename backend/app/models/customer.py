"""
Customer model — a merchant's own customer record (guest or with an email on file),
scoped per-merchant since two different merchants might both have a customer with the same
email.
"""
import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        # Same merchant can't create two customer records with the same email —
        # but two different merchants can each have a customer with that same email.
        UniqueConstraint("merchant_id", "email", name="uq_customers_merchant_email"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=False, index=True)

    # Nullable — a guest checkout customer may never provide an email at all
    email = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    phone = Column(String(32), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)