"""Twilio SMS integration."""

import logging
from typing import Optional, Dict
from datetime import datetime
import uuid

from app.core.config import settings
from app.api.exceptions import BadRequestException

logger = logging.getLogger("kitchenos.sms")


class TwilioSMSProvider:
    """Twilio SMS integration for sending messages.

    pip install twilio
    """

    def __init__(self):
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        self.from_number = getattr(settings, 'TWILIO_FROM_NUMBER', '')
        self._client = None

    def _get_client(self):
        """Lazy initialize Twilio client."""
        if self._client is None:
            try:
                from twilio.rest import Client
                self._client = Client(self.account_sid, self.auth_token)
            except ImportError:
                self._client = MockTwilioClient()
        return self._client

    def send_sms(self, to: str, message: str) -> Dict:
        """Send an SMS message.

        Args:
            to: Recipient phone number (with country code, e.g., +919876543210)
            message: Message body (max 1600 characters)
        """
        if not to.startswith('+'):
            to = f"+91{to}"  # Default to India

        client = self._get_client()

        try:
            sms = client.messages.create(
                body=message[:1600],
                from_=self.from_number,
                to=to
            )

            return {
                "message_id": sms.sid,
                "to": sms.to,
                "status": sms.status,
                "sent_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"SMS send failed: {e}")
            return {
                "error": str(e),
                "to": to,
                "status": "failed"
            }

    def send_order_confirmation(self, phone: str, order_number: str, total: float) -> Dict:
        """Send order confirmation SMS."""
        message = f"Your order #{order_number} has been confirmed! Total: ₹{total:.2f}. Thank you for ordering with KitchenOS."
        return self.send_sms(phone, message)

    def send_order_ready(self, phone: str, order_number: str) -> Dict:
        """Send order ready notification."""
        message = f"Your order #{order_number} is ready for pickup! Please collect it from the counter."
        return self.send_sms(phone, message)

    def send_otp(self, phone: str, otp: str) -> Dict:
        """Send OTP for verification."""
        message = f"Your KitchenOS verification code is: {otp}. Valid for 10 minutes. Do not share this code."
        return self.send_sms(phone, message)

    def get_message_status(self, message_id: str) -> Dict:
        """Get SMS delivery status."""
        client = self._get_client()

        try:
            message = client.messages(message_id).fetch()
            return {
                "message_id": message.sid,
                "status": message.status,
                "to": message.to,
                "error_code": message.error_code,
                "error_message": message.error_message
            }
        except Exception as e:
            return {"error": str(e)}


class MockTwilioClient:
    """Mock Twilio client for development."""

    def __init__(self):
        self.messages = self

    def create(self, body: str, from_: str, to: str) -> object:
        """Mock message creation."""
        logger.info(f"Mock SMS: {to} - {body[:50]}...")
        return type('Message', (), {
            'sid': f"SM{uuid.uuid4().hex[:20]}",
            'to': to,
            'status': 'sent'
        })()

    def fetch(self) -> object:
        return type('Message', (), {
            'sid': 'mock',
            'status': 'delivered',
            'to': '+1234567890',
            'error_code': None,
            'error_message': None
        })()

    def __call__(self, *args, **kwargs):
        return self


# Singleton
sms_provider = TwilioSMSProvider()
