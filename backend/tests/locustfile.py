"""Load testing with Locust.

Install: pip install locust
Run: locust -f tests/locustfile.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between
import random
import string


class KitchenOSUser(HttpUser):
    wait_time = between(1, 3)
    token = None
    branch_id = None

    def on_start(self):
        """Login on start."""
        response = self.client.post("/api/v1/auth/token", data={
            "username": "admin@demo.com",
            "password": "password123"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.branch_id = response.json().get("branch_id")
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(5)
    def get_menu_items(self):
        """Get menu items - most common operation."""
        self.client.get("/api/v1/menu/items", headers=self.headers)

    @task(3)
    def get_menu_categories(self):
        """Get menu categories."""
        self.client.get("/api/v1/menu/categories", headers=self.headers)

    @task(2)
    def create_order(self):
        """Create an order - simulated POS flow."""
        # First get menu items
        response = self.client.get("/api/v1/menu/items", headers=self.headers)
        if response.status_code != 200:
            return

        items = response.json()
        if not items:
            return

        # Select random items
        selected = random.sample(items, min(3, len(items)))

        order_items = []
        for item in selected:
            order_items.append({
                "menu_item_id": item["id"],
                "item_name": item["name"],
                "quantity": random.randint(1, 3),
                "unit_price": float(item["base_price"])
            })

        self.client.post("/api/v1/orders/", json={
            "order_type": "dine_in",
            "items": order_items,
            "branch_id": self.branch_id
        }, headers=self.headers)

    @task(2)
    def get_active_orders(self):
        """Get active orders - kitchen display."""
        self.client.get("/api/v1/orders/active/", headers=self.headers)

    @task(1)
    def get_tables(self):
        """Get tables."""
        if self.branch_id:
            self.client.get(f"/api/v1/tables/?branch_id={self.branch_id}", headers=self.headers)

    @task(1)
    def get_reports(self):
        """Get daily sales report."""
        self.client.get("/api/v1/reports/daily-sales", headers=self.headers)

    @task(1)
    def get_customers(self):
        """Get customers."""
        self.client.get("/api/v1/customers/", headers=self.headers)

    @task(1)
    def search(self):
        """Search."""
        queries = ["chicken", "paneer", "rice", "naan", "biryani"]
        q = random.choice(queries)
        self.client.get(f"/api/v1/search/?q={q}", headers=self.headers)


class AdminUser(HttpUser):
    """Admin operations."""
    wait_time = between(2, 5)
    weight = 1  # Lower weight than POS users

    def on_start(self):
        response = self.client.post("/api/v1/auth/token", data={
            "username": "admin@demo.com",
            "password": "password123"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(2)
    def admin_dashboard(self):
        self.client.get("/api/v1/admin/dashboard", headers=self.headers)

    @task(1)
    def get_reports(self):
        self.client.get("/api/v1/reports/item-wise-sales", headers=self.headers)

    @task(1)
    def get_inventory(self):
        self.client.get("/api/v1/inventory/items", headers=self.headers)

    @task(1)
    def get_low_stock(self):
        self.client.get("/api/v1/inventory/low-stock", headers=self.headers)
