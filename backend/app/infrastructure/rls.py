"""Row-Level Security (RLS) for multi-tenant isolation."""

from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


class RowLevelSecurity:
    """PostgreSQL Row-Level Security policies."""

    TENANT_TABLES = [
        "tenants", "branches", "users", "menu_categories", "menu_items",
        "menu_variants", "menu_modifier_groups", "menu_modifiers",
        "orders", "order_items", "payments", "tax_configs", "coupons",
        "customers", "loyalty_transactions", "inventory_categories",
        "inventory_items", "stock_movements", "vendors", "purchase_orders",
        "shifts", "shift_assignments", "audit_logs"
    ]

    @classmethod
    def enable_rls(cls, db: Session):
        """Enable RLS on all tenant tables."""
        for table in cls.TENANT_TABLES:
            try:
                db.execute(text(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY'))
            except Exception as e:
                logger.warning(f"RLS enable failed for {table}: {e}")
        db.commit()

    @classmethod
    def create_policies(cls, db: Session):
        """Create RLS policies for tenant isolation."""
        for table in cls.TENANT_TABLES:
            try:
                policy_sql = text(f"""
                    CREATE POLICY tenant_isolation_{table} ON "{table}"
                        USING (tenant_id = current_setting('app.current_tenant_id')::VARCHAR)
                        WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::VARCHAR)
                """)
                db.execute(policy_sql)
            except Exception:
                # Policy might already exist
                pass
        db.commit()

    @classmethod
    def set_tenant_context(cls, db: Session, tenant_id: str):
        """Set the current tenant context for RLS.

        Uses parameterized query to prevent SQL injection.
        """
        db.execute(
            text("SELECT set_config('app.current_tenant_id', :tenant_id, false)"),
            {"tenant_id": tenant_id}
        )

    @classmethod
    def disable_rls(cls, db: Session):
        """Disable RLS on all tenant tables (for admin operations)."""
        for table in cls.TENANT_TABLES:
            try:
                db.execute(text(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY'))
            except Exception:
                pass
        db.commit()
