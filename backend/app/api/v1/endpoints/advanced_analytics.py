"""Advanced analytics endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.analytics.advanced import AdvancedAnalyticsService

router = APIRouter()


@router.get("/customer-lifetime-value")
async def customer_lifetime_value(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = AdvancedAnalyticsService(db)
    return service.get_customer_lifetime_value(current_user["tenant_id"])


@router.get("/rfm-segmentation")
async def rfm_segmentation(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = AdvancedAnalyticsService(db)
    return service.get_rfm_segmentation(current_user["tenant_id"])


@router.get("/retention")
async def retention_metrics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = AdvancedAnalyticsService(db)
    return service.get_retention_metrics(current_user["tenant_id"])
