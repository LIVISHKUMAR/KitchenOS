"""Tests for order endpoints."""

import pytest


def _create_menu_item(client, auth_headers, name="Test Item", price=100.00):
    """Helper to create a menu item."""
    cat = client.post("/api/v1/menu/categories", json={"name": "Test Cat"}, headers=auth_headers)
    cat_id = cat.json()["id"]
    item = client.post("/api/v1/menu/items", json={
        "name": name,
        "base_price": price,
        "category_id": cat_id
    }, headers=auth_headers)
    return item.json()


def test_create_order(client, auth_headers):
    """Test creating an order."""
    item = _create_menu_item(client, auth_headers, "Pizza", 299.00)

    response = client.post("/api/v1/orders/", json={
        "order_type": "dine_in",
        "items": [{
            "menu_item_id": item["id"],
            "item_name": "Pizza",
            "quantity": 2,
            "unit_price": 299.00
        }]
    }, headers=auth_headers)

    assert response.status_code == 201
    data = response.json()
    assert data["order_type"] == "dine_in"
    assert data["status"] == "pending"
    assert len(data["items"]) == 1
    assert float(data["subtotal"]) == 598.00


def test_order_total_calculation(client, auth_headers):
    """Test order total calculation with tax."""
    item = _create_menu_item(client, auth_headers, "Burger", 199.00)

    response = client.post("/api/v1/orders/", json={
        "order_type": "takeaway",
        "items": [{
            "menu_item_id": item["id"],
            "item_name": "Burger",
            "quantity": 1,
            "unit_price": 199.00
        }]
    }, headers=auth_headers)

    data = response.json()
    subtotal = float(data["subtotal"])
    tax = float(data["tax_amount"])
    total = float(data["total"])

    assert subtotal == 199.00
    assert tax >= 0  # Tax may be 0 if no tax config
    assert total == subtotal + tax


def test_update_order_status(client, auth_headers):
    """Test order status update."""
    item = _create_menu_item(client, auth_headers)

    # Create order
    create_response = client.post("/api/v1/orders/", json={
        "order_type": "dine_in",
        "items": [{
            "menu_item_id": item["id"],
            "item_name": item["name"],
            "quantity": 1,
            "unit_price": float(item["base_price"])
        }]
    }, headers=auth_headers)
    order_id = create_response.json()["id"]

    # Update status
    response = client.put(f"/api/v1/orders/{order_id}/status?status=confirmed", headers=auth_headers)
    assert response.status_code in (200, 201)
    assert response.json()["status"] == "confirmed"


def test_delete_order(client, auth_headers):
    """Test order soft delete."""
    item = _create_menu_item(client, auth_headers)

    create_response = client.post("/api/v1/orders/", json={
        "order_type": "dine_in",
        "items": [{
            "menu_item_id": item["id"],
            "item_name": item["name"],
            "quantity": 1,
            "unit_price": float(item["base_price"])
        }]
    }, headers=auth_headers)
    order_id = create_response.json()["id"]

    # Delete (soft)
    response = client.delete(f"/api/v1/orders/{order_id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify it's cancelled, not gone
    get_response = client.get(f"/api/v1/orders/{order_id}", headers=auth_headers)
    assert get_response.json()["status"] == "cancelled"


def test_get_active_orders(client, auth_headers):
    """Test getting active orders."""
    item = _create_menu_item(client, auth_headers)

    # Create orders
    client.post("/api/v1/orders/", json={
        "order_type": "dine_in",
        "items": [{"menu_item_id": item["id"], "item_name": item["name"], "quantity": 1, "unit_price": 100}]
    }, headers=auth_headers)

    response = client.get("/api/v1/orders/active/", headers=auth_headers)
    assert response.status_code in (200, 201)
    orders = response.json()
    assert len(orders) >= 1
