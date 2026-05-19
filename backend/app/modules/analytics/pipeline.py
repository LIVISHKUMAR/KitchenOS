"""Analytics data pipeline with materialized views."""

from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text


class AnalyticsPipeline:
    def __init__(self, db: Session):
        self.db = db

    def create_materialized_views(self):
        """Create materialized views for analytics."""
        views = [
            # Daily sales summary
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS daily_sales_mv AS
            SELECT
                tenant_id,
                branch_id,
                DATE(created_at) as sale_date,
                COUNT(*) as order_count,
                SUM(subtotal) as total_subtotal,
                SUM(tax_amount) as total_tax,
                SUM(discount_amount) as total_discount,
                SUM(total) as total_revenue,
                AVG(total) as avg_order_value,
                COUNT(DISTINCT customer_id) as unique_customers
            FROM orders
            WHERE status != 'cancelled'
            GROUP BY tenant_id, branch_id, DATE(created_at)
            """,

            # Item performance
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS item_performance_mv AS
            SELECT
                oi.menu_item_id,
                oi.item_name,
                o.tenant_id,
                o.branch_id,
                DATE(o.created_at) as sale_date,
                SUM(oi.quantity) as total_quantity,
                SUM(oi.total) as total_revenue,
                AVG(oi.unit_price) as avg_price,
                COUNT(DISTINCT o.id) as order_count
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE o.status != 'cancelled'
            GROUP BY oi.menu_item_id, oi.item_name, o.tenant_id, o.branch_id, DATE(o.created_at)
            """,

            # Customer metrics
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS customer_metrics_mv AS
            SELECT
                c.id as customer_id,
                c.tenant_id,
                c.name,
                c.phone,
                c.loyalty_points,
                COUNT(o.id) as total_orders,
                SUM(o.total) as total_spent,
                AVG(o.total) as avg_order_value,
                MAX(o.created_at) as last_order_date,
                MIN(o.created_at) as first_order_date
            FROM customers c
            LEFT JOIN orders o ON c.id = o.customer_id AND o.status != 'cancelled'
            GROUP BY c.id, c.tenant_id, c.name, c.phone, c.loyalty_points
            """,

            # Hourly order distribution
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS hourly_orders_mv AS
            SELECT
                tenant_id,
                branch_id,
                EXTRACT(HOUR FROM created_at) as order_hour,
                DATE(created_at) as order_date,
                COUNT(*) as order_count,
                SUM(total) as total_revenue
            FROM orders
            WHERE status != 'cancelled'
            GROUP BY tenant_id, branch_id, EXTRACT(HOUR FROM created_at), DATE(created_at)
            """,

            # Payment method breakdown
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS payment_breakdown_mv AS
            SELECT
                p.tenant_id,
                p.branch_id,
                p.payment_method,
                DATE(p.created_at) as payment_date,
                COUNT(*) as payment_count,
                SUM(p.amount) as total_amount
            FROM payments p
            WHERE p.status = 'completed'
            GROUP BY p.tenant_id, p.branch_id, p.payment_method, DATE(p.created_at)
            """
        ]

        for view_sql in views:
            try:
                self.db.execute(text(view_sql))
            except Exception as e:
                print(f"View creation failed: {e}")

        self.db.commit()

    def refresh_views(self):
        """Refresh all materialized views."""
        views = [
            "daily_sales_mv",
            "item_performance_mv",
            "customer_metrics_mv",
            "hourly_orders_mv",
            "payment_breakdown_mv"
        ]

        for view in views:
            try:
                self.db.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view}"))
            except Exception:
                try:
                    self.db.execute(text(f"REFRESH MATERIALIZED VIEW {view}"))
                except Exception as e:
                    print(f"Refresh failed for {view}: {e}")

        self.db.commit()

    def get_daily_sales(self, tenant_id: str, branch_id: Optional[str] = None,
                        days_back: int = 30) -> list:
        """Get daily sales from materialized view."""
        query = text("""
            SELECT sale_date, order_count, total_revenue, avg_order_value, unique_customers
            FROM daily_sales_mv
            WHERE tenant_id = :tenant_id
            AND sale_date >= CURRENT_DATE - INTERVAL ':days days'
            ORDER BY sale_date DESC
        """)

        try:
            result = self.db.execute(query, {
                "tenant_id": tenant_id,
                "days": days_back
            })
            return [
                {
                    "date": str(row[0]),
                    "orders": row[1],
                    "revenue": float(row[2] or 0),
                    "avg_order_value": float(row[3] or 0),
                    "customers": row[4]
                }
                for row in result.fetchall()
            ]
        except Exception:
            return []
