"""GraphQL API using Strawberry."""

import strawberry
from typing import List, Optional
from datetime import datetime


@strawberry.type
class MenuItemType:
    id: str
    name: str
    description: Optional[str]
    base_price: float
    is_veg: bool
    is_available: bool
    category_id: Optional[str]
    item_code: Optional[str]


@strawberry.type
class MenuCategoryType:
    id: str
    name: str
    description: Optional[str]
    display_order: int
    items: List[MenuItemType]


@strawberry.type
class OrderItemType:
    id: str
    menu_item_id: str
    item_name: str
    quantity: float
    unit_price: float
    total: float
    prep_status: Optional[str]


@strawberry.type
class OrderType:
    id: str
    order_number: str
    order_type: str
    status: str
    subtotal: float
    tax_amount: float
    total: float
    payment_status: str
    customer_name: Optional[str]
    items: List[OrderItemType]
    created_at: Optional[str]


@strawberry.type
class CustomerType:
    id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    loyalty_points: int
    total_orders: int
    total_spent: float


@strawberry.type
class TenantType:
    id: str
    name: str
    slug: str
    subscription_plan: str


@strawberry.type
class PaymentType:
    id: str
    order_id: str
    amount: float
    payment_method: str
    status: str


@strawberry.type
class DailySalesType:
    date: str
    order_count: int
    total_sales: float
    avg_order_value: float


@strawberry.input
class OrderItemInput:
    menu_item_id: str
    item_name: str
    quantity: float
    unit_price: float


@strawberry.input
class CreateOrderInput:
    order_type: str
    items: List[OrderItemInput]
    table_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None


@strawberry.type
class Query:
    @strawberry.field
    def menu_items(self, category_id: Optional[str] = None) -> List[MenuItemType]:
        # In production, fetch from DB
        return []

    @strawberry.field
    def menu_categories(self) -> List[MenuCategoryType]:
        return []

    @strawberry.field
    def orders(self, status: Optional[str] = None, limit: int = 50) -> List[OrderType]:
        return []

    @strawberry.field
    def order(self, id: str) -> Optional[OrderType]:
        return None

    @strawberry.field
    def customers(self, limit: int = 50) -> List[CustomerType]:
        return []

    @strawberry.field
    def customer(self, id: str) -> Optional[CustomerType]:
        return None

    @strawberry.field
    def daily_sales(self, date: Optional[str] = None) -> Optional[DailySalesType]:
        return None


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_order(self, input: CreateOrderInput) -> OrderType:
        # In production, create order via service
        return OrderType(
            id="new-order-id",
            order_number="ORD-001",
            order_type=input.order_type,
            status="pending",
            subtotal=0,
            tax_amount=0,
            total=0,
            payment_status="pending",
            customer_name=input.customer_name,
            items=[],
            created_at=datetime.utcnow().isoformat()
        )


schema = strawberry.Schema(query=Query, mutation=Mutation)
