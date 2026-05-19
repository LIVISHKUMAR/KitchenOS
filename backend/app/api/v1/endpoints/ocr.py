"""OCR invoice processing endpoints."""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.invoice.ocr import ocr_processor
from app.models import InventoryItem

router = APIRouter()


@router.post("/process")
async def process_invoice(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Process an invoice image using OCR.

    In production, use proper OCR service.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Read image
    image_data = await file.read()

    # Placeholder - in production, send to OCR API
    # For now, return mock data
    return {
        "message": "OCR processing - integrate with OCR API",
        "supported_formats": ["jpg", "png", "pdf"],
        "note": "Configure Google Vision, AWS Textract, or Tesseract for actual OCR"
    }


@router.post("/extract-text")
async def extract_text(
    text: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Extract invoice data from text (for testing OCR results)."""
    result = ocr_processor.process_invoice(text)

    # Try to match with inventory
    if result["items"]:
        inventory_items = db.query(InventoryItem).filter(
            InventoryItem.tenant_id == current_user["tenant_id"],
            InventoryItem.is_active == True
        ).all()

        inv_list = [
            {"id": str(i.id), "name": i.name, "unit": i.unit}
            for i in inventory_items
        ]

        result["matched_items"] = ocr_processor.match_to_inventory(
            result["items"], inv_list
        )

    return result
