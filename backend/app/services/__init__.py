
from pytest import Session
from backend.app.repositories.payment_repository import PaymentRepository
from backend.app.services.ledger_service import LedgerService
from backend.app.services.processor_adapter import get_processor_adapter
from backend.app.services.processor_adapter import get_processor_adapter


def __init__(self, db: Session):
        self.db = db
        self.repo = PaymentRepository(db)
        self.processor = get_processor_adapter()
        self.ledger_service = LedgerService(db)