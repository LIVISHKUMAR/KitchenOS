"""Voice ordering endpoints."""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session

router = APIRouter()


class VoiceOrderParse(BaseModel):
    text: str
    branch_id: Optional[str] = None


@router.post("/parse")
async def parse_voice_order(
    data: VoiceOrderParse,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Parse voice text into order items using NLP.

    In production, use a proper NLP service like:
    - Google Cloud Speech-to-Text + Dialogflow
    - AWS Transcribe + Lex
    - Azure Speech + LUIS
    """
    text = data.text.lower()

    # Simple keyword-based parsing (replace with NLP in production)
    from app.models import MenuItem

    # Get menu items for matching
    items = db.query(MenuItem).filter(
        MenuItem.tenant_id == current_user["tenant_id"],
        MenuItem.is_available == True
    ).all()

    parsed_items = []
    words = text.split()

    # Simple matching: look for menu item names in the text
    for item in items:
        item_name_lower = item.name.lower()
        if item_name_lower in text:
            # Try to extract quantity
            quantity = 1
            for i, word in enumerate(words):
                if word.isdigit() and i + 1 < len(words):
                    if item_name_lower.startswith(words[i + 1]):
                        quantity = int(word)
                        break

            parsed_items.append({
                "menu_item_id": str(item.id),
                "item_name": item.name,
                "quantity": quantity,
                "unit_price": float(item.base_price),
                "confidence": 0.8
            })

    return {
        "original_text": data.text,
        "parsed_items": parsed_items,
        "total_items": len(parsed_items),
        "confidence": 0.7 if parsed_items else 0.0
    }


@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Transcribe audio to text.

    In production, integrate with speech-to-text service.
    """
    # Read audio file
    audio_data = await audio.read()

    # Placeholder - in production, send to speech-to-text API
    return {
        "transcription": "Sample transcription - integrate with speech-to-text API",
        "confidence": 0.0,
        "language": "en",
        "note": "Configure speech-to-text API for actual transcription"
    }
