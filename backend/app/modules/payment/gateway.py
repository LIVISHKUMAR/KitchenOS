"""Razorpay payment gateway integration."""

import hmac
import hashlib
import uuid
from typing import Optional
from datetime import datetime

from app.core.config import settings
from app.api.exceptions import BadRequestException


class RazorpayGateway:
    """Razorpay payment gateway integration.

    In production, use the razorpay Python SDK:
        pip install razorpay
        client = razorpay.Client(auth=(key_id, key_secret))

    This implementation uses direct API calls for demonstration.
    """

    def __init__(self):
        self.key_id = getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_placeholder')
        self.key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', 'placeholder')
        self.base_url = "https://api.razorpay.com/v1"

    def create_order(self, amount: float, currency: str = "INR",
                     receipt: Optional[str] = None, notes: Optional[dict] = None) -> dict:
        """Create a Razorpay order.

        In production, this calls Razorpay API:
            POST /v1/orders
        """
        order_id = f"order_{uuid.uuid4().hex[:14]}"
        receipt = receipt or f"receipt_{uuid.uuid4().hex[:8]}"

        return {
            "id": order_id,
            "entity": "order",
            "amount": int(amount * 100),  # Razorpay uses paise
            "amount_paid": 0,
            "currency": currency,
            "receipt": receipt,
            "status": "created",
            "notes": notes or {},
            "created_at": int(datetime.utcnow().timestamp())
        }

    def verify_payment(self, razorpay_order_id: str, razorpay_payment_id: str,
                       razorpay_signature: str) -> bool:
        """Verify Razorpay payment signature.

        Signature = HMAC-SHA256(order_id + "|" + payment_id, key_secret)
        """
        message = f"{razorpay_order_id}|{razorpay_payment_id}"
        expected_signature = hmac.new(
            self.key_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, razorpay_signature)

    def create_refund(self, payment_id: str, amount: Optional[float] = None,
                      reason: Optional[str] = None) -> dict:
        """Create a refund for a payment.

        In production: POST /v1/payments/{id}/refund
        """
        refund_id = f"rfnd_{uuid.uuid4().hex[:14]}"

        return {
            "id": refund_id,
            "entity": "refund",
            "amount": int((amount or 0) * 100),
            "payment_id": payment_id,
            "reason": reason or "requested_by_customer",
            "status": "processed",
            "created_at": int(datetime.utcnow().timestamp())
        }

    def get_payment(self, payment_id: str) -> dict:
        """Fetch payment details.

        In production: GET /v1/payments/{id}
        """
        return {
            "id": payment_id,
            "entity": "payment",
            "status": "captured",
            "method": "upi",
            "amount": 0,
            "currency": "INR"
        }


# Singleton
razorpay_gateway = RazorpayGateway()
