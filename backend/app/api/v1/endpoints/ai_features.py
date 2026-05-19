"""AI-powered feature endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.ai.demand_forecast import DemandForecastEngine
from app.modules.ai.predictive_inventory import PredictiveInventoryEngine

router = APIRouter()


@router.get("/demand-forecast")
async def demand_forecast(
    target_date: str,
    branch_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get AI-powered demand forecast for a date."""
    engine = DemandForecastEngine(db)
    return engine.forecast_demand(
        tenant_id=current_user["tenant_id"],
        target_date=target_date,
        branch_id=branch_id or current_user.get("branch_id")
    )


@router.get("/inventory-prediction")
async def inventory_prediction(
    days_ahead: int = Query(default=7, le=30),
    branch_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Predict inventory consumption and reorder needs."""
    engine = PredictiveInventoryEngine(db)
    return engine.predict_consumption(
        tenant_id=current_user["tenant_id"],
        branch_id=branch_id or current_user.get("branch_id", ""),
        days_ahead=days_ahead
    )


@router.get("/purchase-suggestions")
async def purchase_suggestions(
    branch_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Auto-generate purchase order suggestions."""
    engine = PredictiveInventoryEngine(db)
    return engine.generate_purchase_orders(
        tenant_id=current_user["tenant_id"],
        branch_id=branch_id or current_user.get("branch_id", "")
    )


@router.get("/waste-analysis")
async def waste_analysis(
    days_back: int = Query(default=30, le=90),
    branch_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Analyze waste patterns."""
    engine = PredictiveInventoryEngine(db)
    return engine.analyze_waste(
        tenant_id=current_user["tenant_id"],
        branch_id=branch_id or current_user.get("branch_id", ""),
        days_back=days_back
    )
