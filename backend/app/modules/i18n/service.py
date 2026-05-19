"""Internationalization (i18n) service."""

from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, JSON, DateTime, Boolean
from datetime import datetime
from app.infrastructure.database import Base
from app.models import generate_uuid
import uuid


class Translation(Base):
    __tablename__ = "translations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)  # menu_item, category, etc.
    entity_id = Column(String(36), nullable=False, index=True)
    locale = Column(String(10), nullable=False)  # en, hi, ta, te, etc.
    field = Column(String(50), nullable=False)  # name, description
    value = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class I18nService:
    # Supported locales
    LOCALES = {
        "en": "English",
        "hi": "Hindi",
        "ta": "Tamil",
        "te": "Telugu",
        "kn": "Kannada",
        "ml": "Malayalam",
        "bn": "Bengali",
        "gu": "Gujarati",
        "mr": "Marathi",
        "pa": "Punjabi"
    }

    # Currency symbols per locale
    CURRENCY_SYMBOLS = {
        "en": "₹",
        "hi": "₹",
        "ta": "₹",
        "te": "₹",
    }

    def __init__(self, db: Session):
        self.db = db

    def set_translation(self, tenant_id: str, entity_type: str, entity_id: str,
                        locale: str, field: str, value: str) -> Translation:
        # Upsert
        existing = self.db.query(Translation).filter(
            Translation.tenant_id == tenant_id,
            Translation.entity_type == entity_type,
            Translation.entity_id == entity_id,
            Translation.locale == locale,
            Translation.field == field
        ).first()

        if existing:
            existing.value = value
            self.db.commit()
            return existing

        translation = Translation(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            locale=locale,
            field=field,
            value=value
        )
        self.db.add(translation)
        self.db.commit()
        self.db.refresh(translation)
        return translation

    def get_translation(self, tenant_id: str, entity_type: str, entity_id: str,
                        locale: str, field: str) -> Optional[str]:
        translation = self.db.query(Translation).filter(
            Translation.tenant_id == tenant_id,
            Translation.entity_type == entity_type,
            Translation.entity_id == entity_id,
            Translation.locale == locale,
            Translation.field == field
        ).first()

        return translation.value if translation else None

    def get_translations(self, tenant_id: str, entity_type: str,
                         entity_id: str, locale: str) -> Dict[str, str]:
        translations = self.db.query(Translation).filter(
            Translation.tenant_id == tenant_id,
            Translation.entity_type == entity_type,
            Translation.entity_id == entity_id,
            Translation.locale == locale
        ).all()

        return {t.field: t.value for t in translations}

    def get_bulk_translations(self, tenant_id: str, entity_type: str,
                              entity_ids: List[str], locale: str) -> Dict[str, Dict[str, str]]:
        translations = self.db.query(Translation).filter(
            Translation.tenant_id == tenant_id,
            Translation.entity_type == entity_type,
            Translation.entity_id.in_(entity_ids),
            Translation.locale == locale
        ).all()

        result = {}
        for t in translations:
            if t.entity_id not in result:
                result[t.entity_id] = {}
            result[t.entity_id][t.field] = t.value

        return result

    def format_currency(self, amount: float, locale: str = "en") -> str:
        symbol = self.CURRENCY_SYMBOLS.get(locale, "₹")
        return f"{symbol}{amount:,.2f}"

    def get_available_locales(self) -> Dict[str, str]:
        return self.LOCALES
