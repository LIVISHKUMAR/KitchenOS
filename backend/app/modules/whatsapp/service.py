"""WhatsApp Business API integration."""

import logging
from typing import Dict, Optional
from datetime import datetime
import uuid

from app.core.config import settings

logger = logging.getLogger("kitchenos.whatsapp")


class WhatsAppService:
    """WhatsApp Business API integration via Twilio or direct.

    Supports: Order confirmation, order ready, feedback request, promotional messages.
    """

    def __init__(self):
        self.provider = getattr(settings, 'WHATSAPP_PROVIDER', 'twilio')  # twilio or direct
        self.twilio_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        self.twilio_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        self.whatsapp_from = getattr(settings, 'WHATSAPP_FROM_NUMBER', '')

    async def send_message(self, to: str, message: str, template: str = None,
                           template_params: dict = None) -> Dict:
        """Send a WhatsApp message."""
        if not to.startswith('+'):
            to = f"+91{to}"

        try:
            if self.provider == 'twilio':
                return await self._send_via_twilio(to, message, template, template_params)
            else:
                return await self._send_direct(to, message, template, template_params)
        except Exception as e:
            logger.error(f"WhatsApp send failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def _send_via_twilio(self, to: str, message: str,
                                template: str = None, params: dict = None) -> Dict:
        """Send via Twilio WhatsApp API."""
        try:
            from twilio.rest import Client
            client = Client(self.twilio_sid, self.twilio_token)

            if template:
                msg = client.messages.create(
                    from_=f'whatsapp:{self.whatsapp_from}',
                    to=f'whatsapp:{to}',
                    content_sid=template,
                    content_variables=str(params or {})
                )
            else:
                msg = client.messages.create(
                    from_=f'whatsapp:{self.whatsapp_from}',
                    to=f'whatsapp:{to}',
                    body=message
                )

            return {
                "status": "sent",
                "message_id": msg.sid,
                "to": to
            }
        except ImportError:
            logger.warning("Twilio not installed, using mock")
            return {"status": "sent", "message_id": f"mock-{uuid.uuid4().hex[:8]}", "to": to}

    async def _send_direct(self, to: str, message: str,
                            template: str = None, params: dict = None) -> Dict:
        """Send via WhatsApp Business API directly."""
        # Placeholder for direct WhatsApp Business API integration
        logger.info(f"WhatsApp (direct) to {to}: {message[:50]}...")
        return {"status": "sent", "message_id": f"direct-{uuid.uuid4().hex[:8]}", "to": to}

    async def send_order_confirmation(self, phone: str, order_number: str,
                                       total: float, items: list) -> Dict:
        """Send order confirmation message."""
        items_text = "\n".join([f"• {i.get('name', '')} x{i.get('quantity', 1)}" for i in items[:5]])
        if len(items) > 5:
            items_text += f"\n... and {len(items) - 5} more items"

        message = (
            f"🎉 Order Confirmed!\n\n"
            f"Order #{order_number}\n\n"
            f"{items_text}\n\n"
            f"Total: ₹{total:.2f}\n\n"
            f"We're preparing your order. Thank you for choosing us!"
        )

        return await self.send_message(phone, message)

    async def send_order_ready(self, phone: str, order_number: str) -> Dict:
        """Send order ready notification."""
        message = (
            f"✅ Order Ready!\n\n"
            f"Order #{order_number} is ready for pickup.\n\n"
            f"Please collect your order from the counter.\n\n"
            f"Thank you!"
        )

        return await self.send_message(phone, message)

    async def send_delivery_update(self, phone: str, order_number: str,
                                    status: str, eta: int = None) -> Dict:
        """Send delivery status update."""
        eta_text = f"\nEstimated time: {eta} minutes" if eta else ""

        message = (
            f"🚚 Delivery Update\n\n"
            f"Order #{order_number}\n"
            f"Status: {status}{eta_text}\n\n"
            f"Thank you for your patience!"
        )

        return await self.send_message(phone, message)

    async def send_feedback_request(self, phone: str, order_number: str,
                                     feedback_url: str = None) -> Dict:
        """Send feedback request after order completion."""
        url_text = f"\n\nRate your experience: {feedback_url}" if feedback_url else ""

        message = (
            f"📝 How was your order?\n\n"
            f"Order #{order_number}\n\n"
            f"We'd love to hear your feedback!{url_text}\n\n"
            f"Thank you for dining with us!"
        )

        return await self.send_message(phone, message)

    async def send_birthday_offer(self, phone: str, customer_name: str,
                                   offer_code: str) -> Dict:
        """Send birthday/anniversary offer."""
        message = (
            f"🎂 Happy Birthday {customer_name}!\n\n"
            f"As a special treat, use code {offer_code}\n"
            f"for 20% off your next order!\n\n"
            f"Valid for 7 days. Thank you for being a valued customer!"
        )

        return await self.send_message(phone, message)


# Singleton
whatsapp_service = WhatsAppService()
