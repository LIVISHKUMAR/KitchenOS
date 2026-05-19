"""Database indexes for performance optimization."""

from sqlalchemy import text
from sqlalchemy.orm import Session


INDEXES = [
    # Orders - most queried table
    "CREATE INDEX IF NOT EXISTS idx_orders_tenant_branch ON orders(tenant_id, branch_id);",
    "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);",
    "CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);",
    "CREATE INDEX IF NOT EXISTS idx_orders_order_number ON orders(order_number);",
    "CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);",
    "CREATE INDEX IF NOT EXISTS idx_orders_source ON orders(source);",

    # Order Items
    "CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);",
    "CREATE INDEX IF NOT EXISTS idx_order_items_menu_item ON order_items(menu_item_id);",
    "CREATE INDEX IF NOT EXISTS idx_order_items_prep_status ON order_items(prep_status);",

    # Menu Items
    "CREATE INDEX IF NOT EXISTS idx_menu_items_tenant_branch ON menu_items(tenant_id, branch_id);",
    "CREATE INDEX IF NOT EXISTS idx_menu_items_category ON menu_items(category_id);",
    "CREATE INDEX IF NOT EXISTS idx_menu_items_available ON menu_items(is_available);",
    "CREATE INDEX IF NOT EXISTS idx_menu_items_item_code ON menu_items(item_code);",

    # Payments
    "CREATE INDEX IF NOT EXISTS idx_payments_order_id ON payments(order_id);",
    "CREATE INDEX IF NOT EXISTS idx_payments_tenant ON payments(tenant_id);",
    "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);",
    "CREATE INDEX IF NOT EXISTS idx_payments_method ON payments(payment_method);",

    # Customers
    "CREATE INDEX IF NOT EXISTS idx_customers_tenant ON customers(tenant_id);",
    "CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(tenant_id, phone);",
    "CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(tenant_id, email);",

    # Inventory
    "CREATE INDEX IF NOT EXISTS idx_inventory_items_tenant_branch ON inventory_items(tenant_id, branch_id);",
    "CREATE INDEX IF NOT EXISTS idx_inventory_items_code ON inventory_items(item_code);",
    "CREATE INDEX IF NOT EXISTS idx_stock_movements_item ON stock_movements(inventory_item_id);",
    "CREATE INDEX IF NOT EXISTS idx_stock_movements_type ON stock_movements(movement_type);",

    # Audit Logs
    "CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant ON audit_logs(tenant_id);",
    "CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);",
    "CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at);",

    # Loyalty
    "CREATE INDEX IF NOT EXISTS idx_loyalty_customer ON loyalty_transactions(customer_id);",
    "CREATE INDEX IF NOT EXISTS idx_loyalty_type ON loyalty_transactions(transaction_type);",

    # Reservations
    "CREATE INDEX IF NOT EXISTS idx_reservations_branch_date ON reservations(branch_id, reservation_time);",
    "CREATE INDEX IF NOT EXISTS idx_reservations_status ON reservations(status);",

    # Feedback
    "CREATE INDEX IF NOT EXISTS idx_feedbacks_tenant ON feedbacks(tenant_id);",
    "CREATE INDEX IF NOT EXISTS idx_feedbacks_rating ON feedbacks(rating);",

    # Webhooks
    "CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_status ON webhook_deliveries(status);",
    "CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_retry ON webhook_deliveries(next_retry_at);",

    # Event Store
    "CREATE INDEX IF NOT EXISTS idx_event_store_aggregate ON event_store(aggregate_type, aggregate_id);",
    "CREATE INDEX IF NOT EXISTS idx_event_store_type ON event_store(event_type);",

    # API Keys
    "CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);",
    "CREATE INDEX IF NOT EXISTS idx_api_keys_tenant ON api_keys(tenant_id);",
]


def create_indexes(db: Session):
    """Create all performance indexes."""
    for index_sql in INDEXES:
        try:
            db.execute(text(index_sql))
        except Exception as e:
            print(f"Index creation failed: {e}")
    db.commit()
    print(f"Created {len(INDEXES)} indexes")


if __name__ == "__main__":
    from app.infrastructure.database import SessionLocal
    db = SessionLocal()
    create_indexes(db)
    db.close()
