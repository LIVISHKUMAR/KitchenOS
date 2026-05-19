"""GraphQL subscriptions for real-time updates."""

import asyncio
import strawberry
from typing import AsyncGenerator
from datetime import datetime


@strawberry.type
class OrderUpdateType:
    order_id: str
    order_number: str
    status: str
    updated_at: str


@strawberry.type
class KOTUpdateType:
    order_id: str
    item_id: str
    item_name: str
    prep_status: str
    updated_at: str


@strawberry.type
class TableUpdateType:
    table_id: str
    table_number: str
    status: str  # available, occupied, reserved
    order_id: str | None
    updated_at: str


# Global event queues for pub/sub
_order_events: asyncio.Queue = asyncio.Queue()
_kot_events: asyncio.Queue = asyncio.Queue()
_table_events: asyncio.Queue = asyncio.Queue()


async def publish_order_update(order_id: str, order_number: str, status: str):
    """Publish order update event."""
    event = OrderUpdateType(
        order_id=order_id,
        order_number=order_number,
        status=status,
        updated_at=datetime.utcnow().isoformat()
    )
    await _order_events.put(event)


async def publish_kot_update(order_id: str, item_id: str, item_name: str, prep_status: str):
    """Publish KOT update event."""
    event = KOTUpdateType(
        order_id=order_id,
        item_id=item_id,
        item_name=item_name,
        prep_status=prep_status,
        updated_at=datetime.utcnow().isoformat()
    )
    await _kot_events.put(event)


async def publish_table_update(table_id: str, table_number: str, status: str, order_id: str = None):
    """Publish table update event."""
    event = TableUpdateType(
        table_id=table_id,
        table_number=table_number,
        status=status,
        order_id=order_id,
        updated_at=datetime.utcnow().isoformat()
    )
    await _table_events.put(event)


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def order_updates(self) -> AsyncGenerator[OrderUpdateType, None]:
        """Subscribe to order status changes."""
        while True:
            event = await _order_events.get()
            yield event

    @strawberry.subscription
    async def kot_updates(self) -> AsyncGenerator[KOTUpdateType, None]:
        """Subscribe to KOT prep status changes."""
        while True:
            event = await _kot_events.get()
            yield event

    @strawberry.subscription
    async def table_updates(self) -> AsyncGenerator[TableUpdateType, None]:
        """Subscribe to table status changes."""
        while True:
            event = await _table_events.get()
            yield event
