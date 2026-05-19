"""GST invoice generation service."""

from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import Order, OrderItem, Tenant, Branch, Payment


class InvoiceService:
    def __init__(self, db: Session):
        self.db = db

    def generate_invoice(self, order_id: str) -> dict:
        """Generate GST-compliant invoice for an order."""
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError("Order not found")

        tenant = self.db.query(Tenant).filter(Tenant.id == order.tenant_id).first()
        branch = self.db.query(Branch).filter(Branch.id == order.branch_id).first()
        items = self.db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
        payments = self.db.query(Payment).filter(
            Payment.order_id == order_id, Payment.status == "completed"
        ).all()

        # Build line items with tax breakdown
        line_items = []
        for item in items:
            base_amount = float(item.unit_price) * float(item.quantity)
            tax_rate = 18.0  # Default GST
            cgst_rate = tax_rate / 2
            sgst_rate = tax_rate / 2
            cgst_amount = base_amount * (cgst_rate / 100)
            sgst_amount = base_amount * (sgst_rate / 100)

            line_items.append({
                "name": item.item_name,
                "hsn_code": "996331",  # Restaurant service HSN
                "quantity": float(item.quantity),
                "unit": "NOS",
                "unit_price": float(item.unit_price),
                "discount": float(item.discount_amount or 0),
                "taxable_amount": base_amount - float(item.discount_amount or 0),
                "cgst_rate": cgst_rate,
                "cgst_amount": round(cgst_amount, 2),
                "sgst_rate": sgst_rate,
                "sgst_amount": round(sgst_amount, 2),
                "igst_rate": 0,
                "igst_amount": 0,
                "total": float(item.total)
            })

        # Totals
        subtotal = float(order.subtotal)
        total_cgst = sum(li["cgst_amount"] for li in line_items)
        total_sgst = sum(li["sgst_amount"] for li in line_items)
        total_tax = total_cgst + total_sgst
        grand_total = float(order.total)

        # Amount in words (simplified)
        def amount_in_words(amount):
            """Convert amount to words for Indian invoices."""
            whole = int(amount)
            paise = int((amount - whole) * 100)
            if whole == 0:
                return "Zero"
            # Simplified — use num2words library in production
            return f"Rupees {whole} and {paise} Paise Only"

        return {
            "invoice_number": f"INV-{order.order_number}",
            "invoice_date": order.created_at.strftime("%d/%m/%Y") if order.created_at else "",
            "due_date": order.created_at.strftime("%d/%m/%Y") if order.created_at else "",

            # Seller details
            "seller": {
                "name": tenant.name if tenant else "",
                "address": branch.address if branch else "",
                "city": branch.city if branch else "",
                "state": branch.state if branch else "",
                "pincode": branch.postal_code if branch else "",
                "gstin": branch.tax_identifier if branch else "",
                "phone": tenant.phone if tenant else "",
                "email": tenant.email if tenant else "",
            },

            # Buyer details
            "buyer": {
                "name": order.customer_name or "Walk-in Customer",
                "phone": order.customer_phone or "",
                "address": "",
                "gstin": "",
            },

            # Order details
            "order_number": order.order_number,
            "order_type": order.order_type,
            "table_id": str(order.table_id) if order.table_id else None,

            # Line items
            "items": line_items,

            # Totals
            "subtotal": subtotal,
            "discount": float(order.discount_amount or 0),
            "taxable_amount": subtotal - float(order.discount_amount or 0),
            "cgst_total": round(total_cgst, 2),
            "sgst_total": round(total_sgst, 2),
            "igst_total": 0,
            "tax_total": round(total_tax, 2),
            "round_off": round(grand_total - (subtotal + total_tax - float(order.discount_amount or 0)), 2),
            "grand_total": grand_total,

            # Amount in words
            "amount_in_words": amount_in_words(grand_total),

            # Payment details
            "payments": [
                {
                    "method": p.payment_method,
                    "amount": float(p.amount),
                    "transaction_id": p.transaction_id,
                    "date": p.processed_at.strftime("%d/%m/%Y %H:%M") if p.processed_at else ""
                }
                for p in payments
            ],

            # Footer
            "terms": "This is a computer-generated invoice.",
            "restaurant_name": tenant.name if tenant else "KitchenOS Restaurant"
        }
