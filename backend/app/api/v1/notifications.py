"""
HTTP route for a merchant to view their own notification history — read-only, since 
notifications are triggered internally by other events, never created directly via the API.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps_apikey import get_merchant_from_api_key, AuthenticatedMerchant
from app.services.notification_service import NotificationService
from app.schemas.notification import NotificationResponse

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
def list_notifications(
    auth: AuthenticatedMerchant = Depends(get_merchant_from_api_key),
    db: Session = Depends(get_db),
):
    service = NotificationService(db)
    return service.list_notifications(auth.merchant.id)