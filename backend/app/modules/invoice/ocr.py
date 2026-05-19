"""OCR invoice processing service."""

import re
from typing import Dict, List, Optional
from datetime import datetime


class OCRInvoiceProcessor:
    """Process vendor invoices using OCR.

    In production, integrate with:
    - Google Cloud Vision API
    - AWS Textract
    - Azure Form Recognizer
    - Tesseract OCR (open source)
    """

    def __init__(self):
        self._vendor_patterns = {
            "invoice_number": [
                r"invoice\s*(?:no|number|#)\s*[:.]?\s*([A-Z0-9-]+)",
                r"inv\s*[:.]?\s*([A-Z0-9-]+)",
            ],
            "date": [
                r"date\s*[:.]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                r"(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{4})",
            ],
            "total": [
                r"total\s*[:.]?\s*(?:rs\.?|₹)?\s*(\d+[,.]?\d*\.?\d*)",
                r"grand\s*total\s*[:.]?\s*(?:rs\.?|₹)?\s*(\d+[,.]?\d*\.?\d*)",
            ],
            "gst_number": [
                r"gst(?:in)?\s*(?:no|number)?\s*[:.]?\s*([0-9A-Z]{15})",
            ],
            "vendor_name": [
                r"(?:from|vendor|supplier)\s*[:.]?\s*(.+?)(?:\n|$)",
            ]
        }

    def process_invoice(self, text: str) -> Dict:
        """Extract data from invoice text."""
        result = {
            "invoice_number": None,
            "date": None,
            "vendor_name": None,
            "gst_number": None,
            "subtotal": None,
            "tax": None,
            "total": None,
            "items": [],
            "confidence": 0.0
        }

        # Extract fields using patterns
        for field, patterns in self._vendor_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    result[field] = match.group(1).strip()
                    break

        # Extract line items
        result["items"] = self._extract_line_items(text)

        # Calculate confidence
        filled_fields = sum(1 for v in result.values() if v is not None and v != [] and v != 0)
        total_fields = len(result) - 1  # Exclude confidence itself
        result["confidence"] = round(filled_fields / total_fields, 2)

        return result

    def _extract_line_items(self, text: str) -> List[Dict]:
        """Extract line items from invoice text."""
        items = []

        # Pattern: item name, quantity, rate, amount
        item_pattern = r"(.+?)\s+(\d+)\s+(?:rs\.?|₹)?\s*(\d+\.?\d*)\s+(?:rs\.?|₹)?\s*(\d+\.?\d*)"
        matches = re.findall(item_pattern, text, re.IGNORECASE)

        for match in matches:
            items.append({
                "name": match[0].strip(),
                "quantity": int(match[1]),
                "rate": float(match[2]),
                "amount": float(match[3])
            })

        return items

    def match_to_inventory(self, extracted_items: List[Dict],
                           inventory_items: List[Dict]) -> List[Dict]:
        """Match OCR items to inventory items."""
        matched = []

        for ocr_item in extracted_items:
            best_match = None
            best_score = 0

            ocr_name = ocr_item["name"].lower()

            for inv_item in inventory_items:
                inv_name = inv_item["name"].lower()

                # Simple string matching (use fuzzy matching in production)
                score = 0
                if ocr_name == inv_name:
                    score = 1.0
                elif ocr_name in inv_name or inv_name in ocr_name:
                    score = 0.8
                elif any(word in inv_name for word in ocr_name.split()):
                    score = 0.5

                if score > best_score:
                    best_score = score
                    best_match = inv_item

            matched.append({
                "ocr_item": ocr_item,
                "matched_inventory": best_match,
                "match_confidence": best_score,
                "auto_match": best_score >= 0.8
            })

        return matched


# Singleton
ocr_processor = OCRInvoiceProcessor()
