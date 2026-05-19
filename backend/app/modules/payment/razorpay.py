"""Live Razorpay payment gateway integration."""

import hmac
import hashlib
import uuid
from typing import Optional, Dict
from datetime import datetime

from app.core.config import settings
from app.api.exceptions import BadRequestException


class RazorpayLiveGateway:
    """Live Razorpay payment gateway integration.

    Uses Razorpay Python SDK for production.
    pip install razorpay
    """

    def __init__(self):
        self.key_id = getattr(settings, 'RAZORPAY_KEY_ID', '')
        self.key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')
        self._client = None

    def _get_client(self):
        """Lazy initialize Razorpay client."""
        if self._client is None:
            try:
                import razorpay
                self._client = razorpay.Client(auth=(self.key_id, self.key_secret))
            except ImportError:
                # Fallback to mock for development
                self._client = MockRazorpayClient()
        return self._client

    def create_order(self, amount: float, currency: str = "INR",
                     receipt: str = None, notes: Dict = None) -> Dict:
        """Create a Razorpay order.

        Args:
            amount: Amount in rupees (will be converted to paise)
            currency: Currency code (default: INR)
            receipt: Receipt number for reference
            notes: Additional notes
        """
        client = self._get_client()

        order_data = {
            "amount": int(amount * 100),  # Convert to paise
            "currency": currency,
            "receipt": receipt or f"receipt_{uuid.uuid4().hex[:8]}",
            "payment_capture": 1,  # Auto capture
            "notes": notes or {}
        }

        try:
            order = client.order.create(data=order_data)
            return {
                "order_id": order["id"],
                "amount": order["amount"],
                "currency": order["currency"],
                "receipt": order["receipt"],
                "status": order["status"],
                "key_id": self.key_id
            }
        except Exception as e:
            raise BadRequestException(f"Failed to create Razorpay order: {str(e)}")

    def verify_payment(self, razorpay_order_id: str, razorpay_payment_id: str,
                       razorpay_signature: str) -> bool:
        """Verify Razorpay payment signature.

        The signature is generated using HMAC-SHA256:
        HMAC-SHA256(order_id + "|" + payment_id, key_secret)
        """
        message = f"{razorpay_order_id}|{razorpay_payment_id}"
        expected_signature = hmac.new(
            self.key_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, razorpay_signature)

    def capture_payment(self, payment_id: str, amount: float) -> Dict:
        """Capture a payment (if auto-capture is disabled)."""
        client = self._get_client()

        try:
            payment = client.payment.capture(payment_id, int(amount * 100))
            return {
                "payment_id": payment["id"],
                "amount": payment["amount"],
                "status": payment["status"],
                "method": payment["method"]
            }
        except Exception as e:
            raise BadRequestException(f"Failed to capture payment: {str(e)}")

    def create_refund(self, payment_id: str, amount: float = None,
                      speed: str = "normal", reason: str = None) -> Dict:
        """Create a refund for a payment.

        Args:
            payment_id: Razorpay payment ID
            amount: Refund amount (None for full refund)
            speed: Refund speed - "normal" or "optimum"
            reason: Reason for refund
        """
        client = self._get_client()

        refund_data = {"speed": speed}
        if amount:
            refund_data["amount"] = int(amount * 100)
        if reason:
            refund_data["notes"] = {"reason": reason}

        try:
            refund = client.payment.refund(payment_id, refund_data)
            return {
                "refund_id": refund["id"],
                "payment_id": refund["payment_id"],
                "amount": refund["amount"],
                "status": refund["status"],
                "speed": refund["speed"]
            }
        except Exception as e:
            raise BadRequestException(f"Failed to create refund: {str(e)}")

    def get_payment(self, payment_id: str) -> Dict:
        """Get payment details."""
        client = self._get_client()

        try:
            payment = client.payment.fetch(payment_id)
            return {
                "payment_id": payment["id"],
                "amount": payment["amount"],
                "currency": payment["currency"],
                "status": payment["status"],
                "method": payment["method"],
                "captured": payment.get("captured", False),
                "created_at": payment.get("created_at")
            }
        except Exception as e:
            raise BadRequestException(f"Failed to fetch payment: {str(e)}")

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """Verify Razorpay webhook signature."""
        expected = hmac.new(
            self.key_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected, signature)


class MockRazorpayClient:
    """Mock Razorpay client for development/testing."""

    def order_create(self, data: Dict) -> Dict:
        return {
            "id": f"order_{uuid.uuid4().hex[:14]}",
            "amount": data.get("amount", 0),
            "currency": data.get("currency", "INR"),
            "receipt": data.get("receipt", ""),
            "status": "created"
        }

    def payment_capture(self, payment_id: str, amount: int) -> Dict:
        return {
            "id": payment_id,
            "amount": amount,
            "status": "captured",
            "method": "card"
        }

    def payment_refund(self, payment_id: str, data: Dict) -> Dict:
        return {
            "id": f"rfnd_{uuid.uuid4().hex[:14]}",
            "payment_id": payment_id,
            "amount": data.get("amount", 0),
            "status": "processed",
            "speed": data.get("speed", "normal")
        }

    def payment_fetch(self, payment_id: str) -> Dict:
        return {
            "id": payment_id,
            "amount": 0,
            "currency": "INR",
            "status": "captured",
            "method": "card",
            "captured": True
        }

    # Aliases for client interface
    def __getattr__(self, name):
        if name == "order":
            return type('obj', (object,), {'create': self.order_create})()
        elif name == "payment":
            return type('obj', (object,), {
                'capture': self.payment_capture,
                'refund': self.payment_refund,
                'fetch': self.payment_fetch
            })()
        raise AttributeError(name)


# Singleton
razorpay_gateway = RazorpayLiveGateway()
