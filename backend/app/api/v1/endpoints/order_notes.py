"""Order notes and history endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.order.notes import OrderNotesService

router = APIRouter()


class NoteCreate(BaseModel):
    order_id: str
    content: str
    note_type: str = "general"


@router.post("/notes")
async def add_order_note(
    data: NoteCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = OrderNotesService(db)
    return service.add_note(
        order_id=data.order_id,
        tenant_id=current_user["tenant_id"],
        user_id=current_user["user_id"],
        content=data.content,
        note_type=data.note_type
    )


@router.get("/{order_id}/notes")
async def get_order_notes(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = OrderNotesService(db)
    return service.get_notes(order_id)


@router.get("/{order_id}/history")
async def get_order_history(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = OrderNotesService(db)
    return service.get_history(order_id)
