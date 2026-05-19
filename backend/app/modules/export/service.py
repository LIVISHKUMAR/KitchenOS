"""Data export service for CSV/Excel generation."""

import csv
import io
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import cast, Date

from app.models import Order, OrderItem, Customer, InventoryItem, Payment


class ExportService:
    def __init__(self, db: Session):
        self.db = db

    def export_orders(self, tenant_id: str, branch_id: Optional[str] = None,
                      date_from: Optional[str] = None, date_to: Optional[str] = None) -> str:
        """Export orders as CSV."""
        query = self.db.query(Order).filter(Order.tenant_id == tenant_id)
        if branch_id:
            query = query.filter(Order.branch_id == branch_id)
        if date_from:
            query = query.filter(cast(Order.created_at, Date) >= date_from)
        if date_to:
            query = query.filter(cast(Order.created_at, Date) <= date_to)

        orders = query.order_by(Order.created_at.desc()).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Order Number", "Date", "Type", "Status", "Customer Name",
            "Subtotal", "Tax", "Discount", "Total", "Payment Status"
        ])

        for order in orders:
            writer.writerow([
                order.order_number,
                order.created_at.strftime("%Y-%m-%d %H:%M") if order.created_at else "",
                order.order_type,
                order.status,
                order.customer_name or "",
                float(order.subtotal or 0),
                float(order.tax_amount or 0),
                float(order.discount_amount or 0),
                float(order.total or 0),
                order.payment_status
            ])

        return output.getvalue()

    def export_order_items(self, tenant_id: str, branch_id: Optional[str] = None,
                           date_from: Optional[str] = None, date_to: Optional[str] = None) -> str:
        """Export order items as CSV."""
        query = self.db.query(OrderItem).join(Order).filter(Order.tenant_id == tenant_id)
        if branch_id:
            query = query.filter(Order.branch_id == branch_id)
        if date_from:
            query = query.filter(cast(Order.created_at, Date) >= date_from)
        if date_to:
            query = query.filter(cast(Order.created_at, Date) <= date_to)

        items = query.all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Order Number", "Item Name", "Item Code", "Quantity",
            "Unit Price", "Tax", "Discount", "Total"
        ])

        for item in items:
            order = self.db.query(Order).filter(Order.id == item.order_id).first()
            writer.writerow([
                order.order_number if order else "",
                item.item_name,
                item.item_code or "",
                float(item.quantity),
                float(item.unit_price),
                float(item.tax_amount or 0),
                float(item.discount_amount or 0),
                float(item.total)
            ])

        return output.getvalue()

    def export_customers(self, tenant_id: str) -> str:
        """Export customers as CSV."""
        customers = self.db.query(Customer).filter(
            Customer.tenant_id == tenant_id
        ).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Name", "Email", "Phone", "Loyalty Points", "Wallet Balance",
            "Total Orders", "Total Spent", "Customer Type", "Membership Tier"
        ])

        for c in customers:
            writer.writerow([
                c.name, c.email or "", c.phone or "",
                c.loyalty_points or 0, float(c.wallet_balance or 0),
                c.total_orders or 0, float(c.total_spent or 0),
                c.customer_type or "", c.membership_tier or ""
            ])

        return output.getvalue()

    def export_inventory(self, tenant_id: str, branch_id: Optional[str] = None) -> str:
        """Export inventory as CSV."""
        query = self.db.query(InventoryItem).filter(
            InventoryItem.tenant_id == tenant_id
        )
        if branch_id:
            query = query.filter(InventoryItem.branch_id == branch_id)

        items = query.all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Name", "Item Code", "Unit", "Current Stock", "Minimum Stock",
            "Reorder Level", "Cost Price", "Selling Price", "Is Trackable"
        ])

        for item in items:
            writer.writerow([
                item.name, item.item_code or "", item.unit,
                float(item.current_stock), float(item.minimum_stock or 0),
                float(item.reorder_level or 0), float(item.cost_price or 0),
                float(item.selling_price or 0), item.is_trackable
            ])

        return output.getvalue()

    def export_payments(self, tenant_id: str, branch_id: Optional[str] = None,
                        date_from: Optional[str] = None, date_to: Optional[str] = None) -> str:
        """Export payments as CSV."""
        query = self.db.query(Payment).filter(Payment.tenant_id == tenant_id)
        if branch_id:
            query = query.filter(Payment.branch_id == branch_id)
        if date_from:
            query = query.filter(cast(Payment.created_at, Date) >= date_from)
        if date_to:
            query = query.filter(cast(Payment.created_at, Date) <= date_to)

        payments = query.order_by(Payment.created_at.desc()).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Payment ID", "Order ID", "Amount", "Method", "Status",
            "Transaction ID", "Processed At"
        ])

        for p in payments:
            writer.writerow([
                str(p.id), str(p.order_id), float(p.amount),
                p.payment_method, p.status,
                p.transaction_id or "",
                p.processed_at.strftime("%Y-%m-%d %H:%M") if p.processed_at else ""
            ])

        return output.getvalue()
