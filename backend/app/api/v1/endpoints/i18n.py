"""Internationalization endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from pydantic import BaseModel
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.i18n.service import I18nService

router = APIRouter()


class TranslationSet(BaseModel):
    entity_type: str
    entity_id: str
    locale: str
    translations: Dict[str, str]  # {"name": "...", "description": "..."}


@router.post("/translations")
async def set_translations(
    data: TranslationSet,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Set translations for an entity."""
    service = I18nService(db)
    results = []
    for field, value in data.translations.items():
        t = service.set_translation(
            current_user["tenant_id"], data.entity_type,
            data.entity_id, data.locale, field, value
        )
        results.append({"field": field, "value": value})
    return {"entity_type": data.entity_type, "entity_id": data.entity_id,
            "locale": data.locale, "translations": results}


@router.get("/translations/{entity_type}/{entity_id}")
async def get_translations(
    entity_type: str,
    entity_id: str,
    locale: str = "en",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get translations for an entity."""
    service = I18nService(db)
    return service.get_translations(current_user["tenant_id"], entity_type, entity_id, locale)


@router.post("/translations/bulk")
async def get_bulk_translations(
    entity_type: str,
    entity_ids: List[str],
    locale: str = "en",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get translations for multiple entities."""
    service = I18nService(db)
    return service.get_bulk_translations(current_user["tenant_id"], entity_type, entity_ids, locale)


@router.get("/locales")
async def get_locales(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get available locales."""
    service = I18nService(db)
    return service.get_available_locales()


@router.get("/format-currency")
async def format_currency(
    amount: float,
    locale: str = "en",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Format currency for a locale."""
    service = I18nService(db)
    return {"amount": amount, "locale": locale, "formatted": service.format_currency(amount, locale)}
