"""Multi-language translation service."""

import uuid
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

# Import the existing Translation model from i18n module
from app.modules.i18n.service import Translation


class TranslationService:
    """Multi-language translation service for Indian restaurants."""

    SUPPORTED_LOCALES = {
        "en": "English",
        "hi": "Hindi (हिन्दी)",
        "ta": "Tamil (தமிழ்)",
        "te": "Telugu (తెలుగు)",
        "kn": "Kannada (ಕನ್ನಡ)",
        "ml": "Malayalam (മലയാളം)",
        "bn": "Bengali (বাংলা)",
        "gu": "Gujarati (ગુજરાતી)",
        "mr": "Marathi (मराठी)",
        "pa": "Punjabi (ਪੰਜਾਬੀ)",
        "ur": "Urdu (اردو)"
    }

    # Common translations for restaurant UI
    UI_TRANSLATIONS = {
        "hi": {
            "menu": "मेनू",
            "orders": "ऑर्डर",
            "cart": "कार्ट",
            "total": "कुल",
            "pay": "भुगतान करें",
            "cash": "नकद",
            "card": "कार्ड",
            "upi": "UPI",
            "subtotal": "उप-योग",
            "tax": "कर",
            "discount": "छूट",
            "table": "टेबल",
            "takeaway": "टेकअवे",
            "delivery": "डिलीवरी",
            "dine_in": "डाइन-इन",
            "order_confirmed": "ऑर्डर की पुष्टि हो गई है",
            "order_ready": "ऑर्डर तैयार है",
            "preparing": "तैयार हो रहा है",
            "completed": "पूरा हो गया",
            "cancelled": "रद्द",
            "search": "खोजें",
            "settings": "सेटिंग्स",
            "logout": "लॉग आउट",
            "print": "प्रिंट",
            "save": "सहेजें",
            "cancel": "रद्द करें",
            "confirm": "पुष्टि करें",
            "add": "जोड़ें",
            "remove": "हटाएं",
            "quantity": "मात्रा",
            "price": "मूल्य",
            "veg": "शाकाहारी",
            "non_veg": "मांसाहारी"
        },
        "ta": {
            "menu": "பட்டியல்",
            "orders": "ஆர்டர்கள்",
            "cart": "வண்டி",
            "total": "மொத்தம்",
            "pay": "பணம் செலுத்து",
            "cash": "ரொக்கம்",
            "card": "அட்டை",
            "table": "மேசை",
            "takeaway": "எடுத்துச் செல்",
            "delivery": "டெலிவரி"
        }
    }

    def __init__(self, db: Session):
        self.db = db

    def set_translation(self, tenant_id: str, entity_type: str,
                        entity_id: str, locale: str, field: str, value: str) -> Translation:
        """Set or update a translation."""
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

    def get_translations(self, tenant_id: str, entity_type: str,
                         entity_id: str, locale: str) -> Dict[str, str]:
        """Get all translations for an entity in a locale."""
        translations = self.db.query(Translation).filter(
            Translation.tenant_id == tenant_id,
            Translation.entity_type == entity_type,
            Translation.entity_id == entity_id,
            Translation.locale == locale
        ).all()

        return {t.field: t.value for t in translations}

    def get_bulk_translations(self, tenant_id: str, entity_type: str,
                              entity_ids: List[str], locale: str) -> Dict[str, Dict[str, str]]:
        """Get translations for multiple entities."""
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

    def get_ui_translations(self, locale: str) -> Dict[str, str]:
        """Get UI string translations."""
        return self.UI_TRANSLATIONS.get(locale, self.UI_TRANSLATIONS.get("en", {}))

    def get_supported_locales(self) -> Dict[str, str]:
        """Get supported locales."""
        return self.SUPPORTED_LOCALES

    def format_currency(self, amount: float, locale: str = "en") -> str:
        """Format currency for locale."""
        # Indian numbering system: 1,00,000 instead of 100,000
        if locale in ("hi", "ta", "te", "kn", "ml", "bn", "gu", "mr", "pa", "ur"):
            return f"₹{self._format_indian(amount)}"
        return f"₹{amount:,.2f}"

    def _format_indian(self, amount: float) -> str:
        """Format number in Indian numbering system."""
        whole = int(amount)
        decimal = int((amount - whole) * 100)

        s = str(whole)
        if len(s) <= 3:
            return f"{s}.{decimal:02d}"

        result = s[-3:]
        s = s[:-3]
        while s:
            result = s[-2:] + "," + result
            s = s[:-2]

        return f"{result}.{decimal:02d}"


# Singleton
translation_service = None


def get_translation_service(db: Session) -> TranslationService:
    global translation_service
    if translation_service is None:
        translation_service = TranslationService(db)
    return translation_service
