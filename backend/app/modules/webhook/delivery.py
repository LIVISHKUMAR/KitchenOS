"""Webhook HTTP delivery with retries."""

import uuid
import hmac
import hashlib
import json
import asyncio
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

import httpx

from app.modules.webhook.service import Webhook, WebhookDelivery, WebhookService


class WebhookDeliveryService:
    def __init__(self, db: Session):
        self.db = db
        self.webhook_service = WebhookService(db)

    async def deliver_webhook(self, delivery_id: str) -> dict:
        """Deliver a single webhook."""
        delivery = self.db.query(WebhookDelivery).filter(
            WebhookDelivery.id == delivery_id
        ).first()

        if not delivery:
            return {"error": "Delivery not found"}

        webhook = self.db.query(Webhook).filter(
            Webhook.id == delivery.webhook_id
        ).first()

        if not webhook or not webhook.is_active:
            return {"error": "Webhook not found or inactive"}

        # Generate signature
        payload_bytes = json.dumps(delivery.payload, sort_keys=True, default=str).encode()
        signature = hmac.new(
            webhook.secret.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": f"sha256={signature}",
            "X-Webhook-Event": delivery.event,
            "X-Webhook-Delivery": str(delivery.id),
            "User-Agent": "KitchenOS-Webhook/1.0"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook.url,
                    json=delivery.payload,
                    headers=headers
                )

            delivery.status = "success" if response.status_code < 400 else "failed"
            delivery.response_code = response.status_code
            delivery.response_body = response.text[:1000]  # Truncate
            delivery.delivered_at = datetime.utcnow()
            delivery.attempts = (delivery.attempts or 0) + 1

            self.db.commit()

            return {
                "delivery_id": str(delivery.id),
                "status": delivery.status,
                "response_code": response.status_code
            }

        except Exception as e:
            delivery.status = "failed"
            delivery.response_body = str(e)[:1000]
            delivery.attempts = (delivery.attempts or 0) + 1

            # Schedule retry with exponential backoff
            max_attempts = delivery.max_attempts or 3
            if delivery.attempts < max_attempts:
                backoff = min(300, 30 * (2 ** (delivery.attempts - 1)))  # 30s, 60s, 120s, 300s max
                delivery.next_retry_at = datetime.utcnow() + timedelta(seconds=backoff)
                delivery.status = "pending"

            self.db.commit()

            return {
                "delivery_id": str(delivery.id),
                "status": "failed",
                "error": str(e),
                "retry_at": delivery.next_retry_at.isoformat() if delivery.next_retry_at else None
            }

    async def process_pending_deliveries(self, limit: int = 50) -> dict:
        """Process pending webhook deliveries."""
        pending = self.db.query(WebhookDelivery).filter(
            WebhookDelivery.status == "pending",
            (WebhookDelivery.next_retry_at == None) | (WebhookDelivery.next_retry_at <= datetime.utcnow())
        ).limit(limit).all()

        results = {"processed": 0, "success": 0, "failed": 0}

        for delivery in pending:
            result = await self.deliver_webhook(str(delivery.id))
            results["processed"] += 1
            if result.get("status") == "success":
                results["success"] += 1
            else:
                results["failed"] += 1

        return results

    def get_delivery_stats(self, webhook_id: str) -> dict:
        """Get delivery statistics for a webhook."""
        deliveries = self.db.query(WebhookDelivery).filter(
            WebhookDelivery.webhook_id == webhook_id
        ).all()

        total = len(deliveries)
        success = sum(1 for d in deliveries if d.status == "success")
        failed = sum(1 for d in deliveries if d.status == "failed")
        pending = sum(1 for d in deliveries if d.status == "pending")

        return {
            "total": total,
            "success": success,
            "failed": failed,
            "pending": pending,
            "success_rate": round((success / max(total, 1)) * 100, 1)
        }
