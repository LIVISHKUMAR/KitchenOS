"""Feedback endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.feedback.service import FeedbackService

router = APIRouter()


class FeedbackCreate(BaseModel):
    branch_id: Optional[str] = None
    order_id: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    rating: int
    food_rating: Optional[int] = None
    service_rating: Optional[int] = None
    ambiance_rating: Optional[int] = None
    comment: Optional[str] = None
    tags: Optional[list] = []


@router.post("/", status_code=201)
async def submit_feedback(
    data: FeedbackCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = FeedbackService(db)
    return service.submit_feedback(current_user["tenant_id"], data.model_dump())


@router.get("/")
async def list_feedbacks(
    branch_id: Optional[str] = None,
    sentiment: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = FeedbackService(db)
    return service.get_feedbacks(current_user["tenant_id"], branch_id, sentiment, skip, limit)


@router.get("/analytics")
async def feedback_analytics(
    branch_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = FeedbackService(db)
    return service.get_analytics(current_user["tenant_id"], branch_id)


@router.put("/{feedback_id}/respond")
async def respond_to_feedback(
    feedback_id: str,
    response: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = FeedbackService(db)
    result = service.respond_to_feedback(feedback_id, response)
    if not result:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return result
