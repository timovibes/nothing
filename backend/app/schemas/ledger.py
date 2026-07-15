# response schemas for viewing wallet balance and ledger entry history.
import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.ledger import LedgerAccountType, LedgerEntryDirection, LedgerEntryType


class WalletBalanceResponse(BaseModel):
    currency: str
    available_balance_minor: int
    total_settled_minor: int
    updated_at: datetime

    model_config = {"from_attributes": True}


class LedgerEntryResponse(BaseModel):
    id: uuid.UUID
    transaction_group_id: uuid.UUID
    account_type: LedgerAccountType
    direction: LedgerEntryDirection
    amount_minor: int
    currency: str
    entry_type: LedgerEntryType
    reference_id: uuid.UUID | None
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}