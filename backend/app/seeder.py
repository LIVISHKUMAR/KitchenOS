"""Database seeder for development and demo purposes."""

import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.infrastructure.database import SessionLocal, engine, Base
from app.models import (
    Tenant, Branch, User, MenuCategory, MenuItem, MenuVariant,
    MenuModifierGroup, MenuModifier, DiningTable, TaxConfig,
    Customer, InventoryItem, Vendor, Shift
)
from app.core.security import get_password_hash


def seed_database():
    """Seed database with sample data."""
    db = SessionLocal()

    try:
        # Check if already seeded
        existing = db.query(Tenant).first()
        if existing:
            print("Database already seeded. Skipping.")
            return

        print("Seeding database...")

        # Create Tenant
        tenant_id = str(uuid.uuid4())
        tenant = Tenant(
            id=tenant_id,
            name="Demo Restaurant",
            slug="demo-restaurant",
            email="admin@demo-restaurant.com",
            phone="9876543210",
            subscription_plan="professional",
            subscription_status="active",
            max_branches=5,
            max_users=50,
            max_terminals=10,
            is_active=True
        )
        db.add(tenant)

        # Create Branch
        branch_id = str(uuid.uuid4())
        branch = Branch(
            id=branch_id,
            tenant_id=tenant_id,
            name="Demo Restaurant - Main",
            code="MAIN",
            address="123 Main Street",
            city="Mumbai",
            state="Maharashtra",
            postal_code="400001",
            country="India",
            phone="9876543210",
            timezone="Asia/Kolkata",
            currency="INR",
            is_active=True
        )
        db.add(branch)

        # Create Users
        users = [
            {"email": "admin@demo.com", "first_name": "Admin", "last_name": "User", "role": "admin"},
            {"email": "manager@demo.com", "first_name": "Raj", "last_name": "Kumar", "role": "manager"},
            {"email": "cashier@demo.com", "first_name": "Priya", "last_name": "Sharma", "role": "cashier"},
            {"email": "chef@demo.com", "first_name": "Chef", "last_name": "Singh", "role": "chef"},
            {"email": "waiter@demo.com", "first_name": "Amit", "last_name": "Patel", "role": "waiter"},
        ]

        for u in users:
            user = User(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                branch_id=branch_id,
                email=u["email"],
                password_hash=get_password_hash("password123"),
                first_name=u["first_name"],
                last_name=u["last_name"],
                role=u["role"],
                is_active=True
            )
            db.add(user)

        # Create Menu Categories
        categories = [
            {"name": "Starters", "display_order": 1},
            {"name": "Main Course", "display_order": 2},
            {"name": "Breads", "display_order": 3},
            {"name": "Rice & Biryani", "display_order": 4},
            {"name": "Desserts", "display_order": 5},
            {"name": "Beverages", "display_order": 6},
        ]

        cat_ids = {}
        for c in categories:
            cat_id = str(uuid.uuid4())
            cat_ids[c["name"]] = cat_id
            category = MenuCategory(
                id=cat_id,
                tenant_id=tenant_id,
                branch_id=branch_id,
                name=c["name"],
                display_order=c["display_order"],
                is_active=True
            )
            db.add(category)

        # Create Menu Items
        items = [
            # Starters
            {"name": "Paneer Tikka", "category": "Starters", "price": 249, "is_veg": True, "code": "ST001"},
            {"name": "Chicken 65", "category": "Starters", "price": 299, "is_veg": False, "code": "ST002"},
            {"name": "Veg Spring Rolls", "category": "Starters", "price": 199, "is_veg": True, "code": "ST003"},
            {"name": "Fish Fry", "category": "Starters", "price": 349, "is_veg": False, "code": "ST004"},
            # Main Course
            {"name": "Butter Chicken", "category": "Main Course", "price": 349, "is_veg": False, "code": "MC001"},
            {"name": "Paneer Butter Masala", "category": "Main Course", "price": 299, "is_veg": True, "code": "MC002"},
            {"name": "Dal Makhani", "category": "Main Course", "price": 249, "is_veg": True, "code": "MC003"},
            {"name": "Mutton Rogan Josh", "category": "Main Course", "price": 449, "is_veg": False, "code": "MC004"},
            # Breads
            {"name": "Butter Naan", "category": "Breads", "price": 60, "is_veg": True, "code": "BR001"},
            {"name": "Garlic Naan", "category": "Breads", "price": 70, "is_veg": True, "code": "BR002"},
            {"name": "Tandoori Roti", "category": "Breads", "price": 40, "is_veg": True, "code": "BR003"},
            # Rice & Biryani
            {"name": "Chicken Biryani", "category": "Rice & Biryani", "price": 299, "is_veg": False, "code": "RB001"},
            {"name": "Veg Biryani", "category": "Rice & Biryani", "price": 249, "is_veg": True, "code": "RB002"},
            {"name": "Jeera Rice", "category": "Rice & Biryani", "price": 149, "is_veg": True, "code": "RB003"},
            # Desserts
            {"name": "Gulab Jamun", "category": "Desserts", "price": 129, "is_veg": True, "code": "DS001"},
            {"name": "Rasmalai", "category": "Desserts", "price": 149, "is_veg": True, "code": "DS002"},
            {"name": "Ice Cream", "category": "Desserts", "price": 99, "is_veg": True, "code": "DS003"},
            # Beverages
            {"name": "Masala Chai", "category": "Beverages", "price": 60, "is_veg": True, "code": "BV001"},
            {"name": "Cold Coffee", "category": "Beverages", "price": 120, "is_veg": True, "code": "BV002"},
            {"name": "Fresh Lime Soda", "category": "Beverages", "price": 80, "is_veg": True, "code": "BV003"},
        ]

        for item in items:
            menu_item = MenuItem(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                branch_id=branch_id,
                category_id=cat_ids[item["category"]],
                name=item["name"],
                item_code=item["code"],
                base_price=item["price"],
                tax_rate=5.0,
                is_veg=item["is_veg"],
                is_available=True,
                preparation_time_minutes=15
            )
            db.add(menu_item)

        # Create Dining Tables
        for i in range(1, 11):
            table = DiningTable(
                id=str(uuid.uuid4()),
                branch_id=branch_id,
                table_number=f"T{i}",
                capacity=4 if i <= 6 else 6,
                section="Main" if i <= 6 else "Private",
                is_active=True
            )
            db.add(table)

        # Create Tax Config
        tax = TaxConfig(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            branch_id=branch_id,
            name="GST",
            rate=5.0,
            tax_type="gst",
            applicable_to=["dine_in", "takeaway", "delivery"],
            is_active=True
        )
        db.add(tax)

        # Create Customers
        customers = [
            {"name": "Rahul Verma", "phone": "9876543211", "email": "rahul@email.com"},
            {"name": "Sneha Gupta", "phone": "9876543212", "email": "sneha@email.com"},
            {"name": "Vikram Singh", "phone": "9876543213", "email": "vikram@email.com"},
        ]

        for c in customers:
            customer = Customer(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                name=c["name"],
                phone=c["phone"],
                email=c["email"],
                loyalty_points=100,
                customer_type="regular"
            )
            db.add(customer)

        # Create Inventory Items
        inv_items = [
            {"name": "Chicken", "unit": "kg", "stock": 50, "min": 10, "cost": 250},
            {"name": "Paneer", "unit": "kg", "stock": 30, "min": 5, "cost": 300},
            {"name": "Rice", "unit": "kg", "stock": 100, "min": 20, "cost": 60},
            {"name": "Oil", "unit": "l", "stock": 20, "min": 5, "cost": 120},
            {"name": "Onions", "unit": "kg", "stock": 40, "min": 10, "cost": 30},
            {"name": "Tomatoes", "unit": "kg", "stock": 35, "min": 10, "cost": 40},
        ]

        for inv in inv_items:
            item = InventoryItem(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                branch_id=branch_id,
                name=inv["name"],
                unit=inv["unit"],
                current_stock=inv["stock"],
                minimum_stock=inv["min"],
                cost_price=inv["cost"],
                is_trackable=True,
                is_active=True
            )
            db.add(item)

        # Create Vendor
        vendor = Vendor(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name="Fresh Farms Supplier",
            contact_person="Mr. Sharma",
            phone="9876543220",
            email="sharma@freshfarms.com",
            is_active=True
        )
        db.add(vendor)

        # Create Shifts
        shifts = [
            {"name": "Morning", "start": "09:00", "end": "17:00"},
            {"name": "Evening", "start": "17:00", "end": "01:00"},
        ]

        for s in shifts:
            shift = Shift(
                id=str(uuid.uuid4()),
                branch_id=branch_id,
                name=s["name"],
                start_time=datetime.strptime(s["start"], "%H:%M").time(),
                end_time=datetime.strptime(s["end"], "%H:%M").time(),
                break_duration_minutes=30,
                is_active=True
            )
            db.add(shift)

        db.commit()
        print(f"Seeded successfully!")
        print(f"  Tenant: Demo Restaurant")
        print(f"  Branch: Demo Restaurant - Main")
        print(f"  Users: admin@demo.com / password123")
        print(f"  Menu: {len(items)} items in {len(categories)} categories")
        print(f"  Tables: 10")
        print(f"  Customers: {len(customers)}")
        print(f"  Inventory: {len(inv_items)} items")

    except Exception as e:
        db.rollback()
        print(f"Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
