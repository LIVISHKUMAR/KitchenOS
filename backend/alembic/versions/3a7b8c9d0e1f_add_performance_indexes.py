"""add performance indexes

Revision ID: 3a7b8c9d0e1f
Revises: e596aba7f1f8
Create Date: 2026-05-21 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a7b8c9d0e1f'
down_revision: Union[str, None] = 'e596aba7f1f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Orders - most queried table
    op.create_index('ix_orders_tenant_branch_created', 'orders', ['tenant_id', 'branch_id', 'created_at'])
    op.create_index('ix_orders_tenant_status', 'orders', ['tenant_id', 'status'])
    op.create_index('ix_orders_tenant_payment_status', 'orders', ['tenant_id', 'payment_status'])
    op.create_index('ix_orders_order_number', 'orders', ['order_number'])
    op.create_index('ix_orders_aggregator_order_id', 'orders', ['aggregator_order_id'])

    # Order Items
    op.create_index('ix_order_items_order_id', 'order_items', ['order_id'])
    op.create_index('ix_order_items_prep_status', 'order_items', ['prep_status'])

    # Payments
    op.create_index('ix_payments_order_id', 'payments', ['order_id'])
    op.create_index('ix_payments_tenant_branch', 'payments', ['tenant_id', 'branch_id'])
    op.create_index('ix_payments_idempotency_key', 'payments', ['idempotency_key'], unique=True)
    op.create_index('ix_payments_status', 'payments', ['status'])

    # Menu Items
    op.create_index('ix_menu_items_tenant_branch', 'menu_items', ['tenant_id', 'branch_id'])
    op.create_index('ix_menu_items_category', 'menu_items', ['category_id'])
    op.create_index('ix_menu_items_available', 'menu_items', ['tenant_id', 'is_available'])
    op.create_index('ix_menu_items_item_code', 'menu_items', ['item_code'])

    # Menu Categories
    op.create_index('ix_menu_categories_tenant_branch', 'menu_categories', ['tenant_id', 'branch_id'])

    # Customers
    op.create_index('ix_customers_tenant_phone', 'customers', ['tenant_id', 'phone'])
    op.create_index('ix_customers_tenant_email', 'customers', ['tenant_id', 'email'])

    # Inventory Items
    op.create_index('ix_inventory_items_tenant_branch', 'inventory_items', ['tenant_id', 'branch_id'])
    op.create_index('ix_inventory_items_low_stock', 'inventory_items', ['tenant_id', 'branch_id', 'current_stock', 'minimum_stock'])

    # Stock Movements
    op.create_index('ix_stock_movements_item', 'stock_movements', ['inventory_item_id'])
    op.create_index('ix_stock_movements_branch', 'stock_movements', ['branch_id', 'created_at'])

    # Dining Tables
    op.create_index('ix_dining_tables_branch', 'dining_tables', ['branch_id'])
    op.create_index('ix_dining_tables_current_order', 'dining_tables', ['current_order_id'])

    # Audit Logs
    op.create_index('ix_audit_logs_tenant_created', 'audit_logs', ['tenant_id', 'created_at'])
    op.create_index('ix_audit_logs_user', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'])

    # Purchase Orders
    op.create_index('ix_purchase_orders_tenant_branch', 'purchase_orders', ['tenant_id', 'branch_id'])
    op.create_index('ix_purchase_orders_status', 'purchase_orders', ['tenant_id', 'status'])

    # Shifts
    op.create_index('ix_shifts_branch', 'shifts', ['branch_id'])

    # Shift Assignments
    op.create_index('ix_shift_assignments_user_date', 'shift_assignments', ['user_id', 'date'])

    # Loyalty Transactions
    op.create_index('ix_loyalty_transactions_customer', 'loyalty_transactions', ['customer_id'])

    # Users
    op.create_index('ix_users_tenant_branch', 'users', ['tenant_id', 'branch_id'])
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Branches
    op.create_index('ix_branches_tenant', 'branches', ['tenant_id'])


def downgrade() -> None:
    # Drop all indexes in reverse order
    op.drop_index('ix_branches_tenant')
    op.drop_index('ix_users_email')
    op.drop_index('ix_users_tenant_branch')
    op.drop_index('ix_loyalty_transactions_customer')
    op.drop_index('ix_shift_assignments_user_date')
    op.drop_index('ix_shifts_branch')
    op.drop_index('ix_purchase_orders_status')
    op.drop_index('ix_purchase_orders_tenant_branch')
    op.drop_index('ix_audit_logs_resource')
    op.drop_index('ix_audit_logs_user')
    op.drop_index('ix_audit_logs_tenant_created')
    op.drop_index('ix_dining_tables_current_order')
    op.drop_index('ix_dining_tables_branch')
    op.drop_index('ix_stock_movements_branch')
    op.drop_index('ix_stock_movements_item')
    op.drop_index('ix_inventory_items_low_stock')
    op.drop_index('ix_inventory_items_tenant_branch')
    op.drop_index('ix_customers_tenant_email')
    op.drop_index('ix_customers_tenant_phone')
    op.drop_index('ix_menu_categories_tenant_branch')
    op.drop_index('ix_menu_items_item_code')
    op.drop_index('ix_menu_items_available')
    op.drop_index('ix_menu_items_category')
    op.drop_index('ix_menu_items_tenant_branch')
    op.drop_index('ix_payments_status')
    op.drop_index('ix_payments_idempotency_key')
    op.drop_index('ix_payments_tenant_branch')
    op.drop_index('ix_payments_order_id')
    op.drop_index('ix_order_items_prep_status')
    op.drop_index('ix_order_items_order_id')
    op.drop_index('ix_orders_aggregator_order_id')
    op.drop_index('ix_orders_order_number')
    op.drop_index('ix_orders_tenant_payment_status')
    op.drop_index('ix_orders_tenant_status')
    op.drop_index('ix_orders_tenant_branch_created')
