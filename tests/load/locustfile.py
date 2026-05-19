"""KitchenOS Load Testing Scenarios.

Install: pip install locust
Run: locust -f locustfile.py --host=http://localhost:8000

Scenarios:
1. POS User: Normal billing operations
2. Kitchen: KOT management
3. Admin: Reports and management
4. Peak Hour: High concurrent load
"""

from locust import HttpUser, task, between, events
import random
import string
import json


class POSUser(HttpUser):
    """Simulates a POS cashier during normal operations."""
    wait_time = between(1, 3)
    weight = 5  # Most common user type

    def on_start(self):
        """Login and get token."""
        response = self.client.post("/api/v1/auth/token", data={
            "username": "admin@demo.com",
            "password": "password123"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.branch_id = response.json().get("branch_id")
        else:
            self.token = None
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(10)
    def get_menu(self):
        """Get menu items - most frequent operation."""
        self.client.get("/api/v1/menu/items", headers=self.headers)

    @task(5)
    def get_categories(self):
        """Get menu categories."""
        self.client.get("/api/v1/menu/categories", headers=self.headers)

    @task(3)
    def create_order(self):
        """Create an order - core billing operation."""
        # Get menu items first
        response = self.client.get("/api/v1/menu/items", headers=self.headers)
        if response.status_code != 200:
            return

        items = response.json()
        if not items:
            return

        # Select 1-3 random items
        selected = random.sample(items, min(random.randint(1, 3), len(items)))

        order_items = [{
            "menu_item_id": item["id"],
            "item_name": item["name"],
            "quantity": random.randint(1, 3),
            "unit_price": float(item["base_price"])
        } for item in selected]

        self.client.post("/api/v1/fast-billing/quick-order", json={
            "order_type": random.choice(["dine_in", "takeaway"]),
            "items": order_items,
            "source": "pos"
        }, headers=self.headers)

    @task(2)
    def get_active_orders(self):
        """Get active orders."""
        self.client.get("/api/v1/orders/active/", headers=self.headers)

    @task(1)
    def get_tables(self):
        """Get table status."""
        if self.branch_id:
            self.client.get(f"/api/v1/tables/?branch_id={self.branch_id}", headers=self.headers)


class KitchenUser(HttpUser):
    """Simulates kitchen display operations."""
    wait_time = between(2, 5)
    weight = 2

    def on_start(self):
        response = self.client.post("/api/v1/auth/token", data={
            "username": "chef@demo.com",
            "password": "password123"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
        else:
            self.token = None
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(5)
    def get_kot_orders(self):
        """Get KOT orders - primary kitchen operation."""
        self.client.get("/api/v1/kot/", headers=self.headers)

    @task(3)
    def get_kot_summary(self):
        """Get KOT summary."""
        self.client.get("/api/v1/kot/summary", headers=self.headers)

    @task(1)
    def get_menu(self):
        """Check menu for reference."""
        self.client.get("/api/v1/menu/items", headers=self.headers)


class AdminUser(HttpUser):
    """Simulates admin/manager operations."""
    wait_time = between(5, 10)
    weight = 1

    def on_start(self):
        response = self.client.post("/api/v1/auth/token", data={
            "username": "admin@demo.com",
            "password": "password123"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
        else:
            self.token = None
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(3)
    def get_dashboard(self):
        """Get admin dashboard."""
        self.client.get("/api/v1/admin/dashboard", headers=self.headers)

    @task(2)
    def get_daily_sales(self):
        """Get daily sales report."""
        self.client.get("/api/v1/reports/daily-sales", headers=self.headers)

    @task(2)
    def get_item_sales(self):
        """Get item-wise sales."""
        self.client.get("/api/v1/reports/item-wise-sales", headers=self.headers)

    @task(1)
    def get_inventory(self):
        """Check inventory."""
        self.client.get("/api/v1/inventory/items", headers=self.headers)

    @task(1)
    def get_low_stock(self):
        """Check low stock items."""
        self.client.get("/api/v1/inventory/low-stock", headers=self.headers)

    @task(1)
    def get_customers(self):
        """Get customer list."""
        self.client.get("/api/v1/customers/", headers=self.headers)


class PeakHourUser(HttpUser):
    """Simulates peak hour load with rapid operations."""
    wait_time = between(0.5, 1.5)  # Faster pace
    weight = 3

    def on_start(self):
        response = self.client.post("/api/v1/auth/token", data={
            "username": "admin@demo.com",
            "password": "password123"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
        else:
            self.token = None
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(10)
    def rapid_order(self):
        """Rapid order creation - peak hour simulation."""
        response = self.client.get("/api/v1/menu/items", headers=self.headers)
        if response.status_code != 200:
            return

        items = response.json()
        if not items:
            return

        selected = random.choice(items)

        self.client.post("/api/v1/fast-billing/quick-order", json={
            "order_type": "dine_in",
            "items": [{
                "menu_item_id": selected["id"],
                "item_name": selected["name"],
                "quantity": 1,
                "unit_price": float(selected["base_price"])
            }],
            "source": "pos"
        }, headers=self.headers)

    @task(5)
    def rapid_menu_check(self):
        """Rapid menu check."""
        self.client.get("/api/v1/menu/items", headers=self.headers)
