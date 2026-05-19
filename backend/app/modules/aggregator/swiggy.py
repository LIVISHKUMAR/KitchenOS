"""Swiggy Partner API Integration."""

import uuid
import hmac
import hashlib
import httpx
import logging
from typing import Dict, Optional, List
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger("kitchenos.swiggy")


class SwiggyIntegration:
    """Swiggy Partner API integration for receiving and managing orders.

    Swiggy API Documentation: https://developer.swiggy.com/
    """

    def __init__(self):
        self.base_url = getattr(settings, 'SWIGGY_API_URL', 'https://partner-api.swiggy.com/v1')
        self.client_id = getattr(settings, 'SWIGGY_CLIENT_ID', '')
        self.client_secret = getattr(settings, 'SWIGGY_CLIENT_SECRET', '')
        self.restaurant_id = getattr(settings, 'SWIGGY_RESTAURANT_ID', '')

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """Verify Swiggy webhook signature."""
        expected = hmac.new(
            self.client_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def normalize_order(self, swiggy_order: dict) -> dict:
        """Convert Swiggy order format to KitchenOS format."""
        items = []
        for item in swiggy_order.get("items", []):
            items.append({
                "menu_item_id": item.get("item_id"),  # Need mapping
                "item_name": item.get("name", ""),
                "quantity": item.get("quantity", 1),
                "unit_price": float(item.get("price", 0)) / 100,  # Swiggy uses paise
                "variant_name": item.get("variant_name"),
                "modifiers": [
                    {"name": g.get("name"), "price": float(g.get("price", 0)) / 100}
                    for g in item.get("addons", [])
                ]
            })

        return {
            "aggregator": "swiggy",
            "aggregator_order_id": swiggy_order.get("order_id"),
            "order_type": "delivery",
            "customer_name": swiggy_order.get("customer", {}).get("name", "Swiggy Customer"),
            "customer_phone": swiggy_order.get("customer", {}).get("phone"),
            "delivery_address": swiggy_order.get("delivery_address", {}),
            "items": items,
            "subtotal": float(swiggy_order.get("subtotal", 0)) / 100,
            "tax": float(swiggy_order.get("tax", 0)) / 100,
            "delivery_fee": float(swiggy_order.get("delivery_fee", 0)) / 100,
            "total": float(swiggy_order.get("total", 0)) / 100,
            "special_instructions": swiggy_order.get("special_instructions"),
            "scheduled_at": swiggy_order.get("scheduled_at"),
            "payment_method": "prepaid"  # Swiggy handles payment
        }

    async def update_order_status(self, swiggy_order_id: str, status: str,
                                    estimated_time: int = None) -> Dict:
        """Update order status back to Swiggy."""
        status_map = {
            "confirmed": "accepted",
            "preparing": "food_ready",
            "ready": "dispatched",
            "cancelled": "cancelled"
        }

        swiggy_status = status_map.get(status, status)

        payload = {
            "order_id": swiggy_order_id,
            "status": swiggy_status,
            "restaurant_id": self.restaurant_id
        }

        if estimated_time:
            payload["estimated_delivery_time"] = estimated_time

        # In production, make API call to Swiggy
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         f"{self.base_url}/orders/{swiggy_order_id}/status",
        #         json=payload,
        #         headers={"Authorization": f"Bearer {self._get_token()}"}
        #     )

        logger.info(f"Swiggy status update: {swiggy_order_id} → {swiggy_status}")
        return {"status": "sent", "swiggy_status": swiggy_status}

    async def push_menu(self, menu_items: List[dict]) -> Dict:
        """Push menu updates to Swiggy."""
        swiggy_items = []
        for item in menu_items:
            swiggy_items.append({
                "item_id": item.get("id"),
                "name": item.get("name"),
                "description": item.get("description", ""),
                "price": int(item.get("price", 0) * 100),  # Convert to paise
                "is_veg": item.get("is_veg", True),
                "is_available": item.get("is_available", True),
                "category": item.get("category_name", ""),
                "image_url": item.get("image_url", "")
            })

        # In production, push to Swiggy API
        logger.info(f"Swiggy menu push: {len(swiggy_items)} items")
        return {"status": "pushed", "items": len(swiggy_items)}


class ZomatoIntegration:
    """Zomato Partner API integration."""

    def __init__(self):
        self.base_url = getattr(settings, 'ZOMATO_API_URL', 'https://api.zomato.com/v1')
        self.api_key = getattr(settings, 'ZOMATO_API_KEY', '')
        self.restaurant_id = getattr(settings, 'ZOMATO_RESTAURANT_ID', '')

    def normalize_order(self, zomato_order: dict) -> dict:
        """Convert Zomato order format to KitchenOS format."""
        items = []
        for item in zomato_order.get("items", []):
            items.append({
                "menu_item_id": item.get("item_id"),
                "item_name": item.get("name", ""),
                "quantity": item.get("quantity", 1),
                "unit_price": float(item.get("price", 0)),
                "variant_name": item.get("variant"),
                "modifiers": [
                    {"name": a.get("name"), "price": float(a.get("price", 0))}
                    for a in item.get("add_ons", [])
                ]
            })

        return {
            "aggregator": "zomato",
            "aggregator_order_id": zomato_order.get("order_id"),
            "order_type": "delivery",
            "customer_name": zomato_order.get("user", {}).get("name", "Zomato Customer"),
            "customer_phone": zomato_order.get("user", {}).get("phone"),
            "delivery_address": zomato_order.get("delivery_address", {}),
            "items": items,
            "subtotal": float(zomato_order.get("subtotal", 0)),
            "tax": float(zomato_order.get("tax", 0)),
            "delivery_fee": float(zomato_order.get("delivery_charges", 0)),
            "total": float(zomato_order.get("total", 0)),
            "special_instructions": zomato_order.get("instructions"),
            "scheduled_at": zomato_order.get("scheduled_time"),
            "payment_method": "prepaid"
        }

    async def update_order_status(self, zomato_order_id: str, status: str,
                                    estimated_time: int = None) -> Dict:
        """Update order status back to Zomato."""
        status_map = {
            "confirmed": "accepted",
            "preparing": "preparing",
            "ready": "ready",
            "cancelled": "cancelled"
        }

        zomato_status = status_map.get(status, status)

        logger.info(f"Zomato status update: {zomato_order_id} → {zomato_status}")
        return {"status": "sent", "zomato_status": zomato_status}


# Singletons
swiggy = SwiggyIntegration()
zomato = ZomatoIntegration()
