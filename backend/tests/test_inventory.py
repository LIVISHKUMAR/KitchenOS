"""Tests for inventory endpoints."""

import pytest


def test_create_inventory_item(client, auth_headers):
    """Test creating an inventory item."""
    response = client.post("/api/v1/inventory/items", json={
        "name": "Tomatoes",
        "item_code": "TOM001",
        "unit": "kg",
        "current_stock": 50.0,
        "minimum_stock": 10.0,
        "cost_price": 40.00,
        "selling_price": 60.00,
        "is_trackable": True
    }, headers=auth_headers)

    assert response.status_code in (200, 201)
    data = response.json()
    assert data["name"] == "Tomatoes"


def test_low_stock_alert(client, auth_headers):
    """Test low stock detection."""
    # Create item with low stock
    client.post("/api/v1/inventory/items", json={
        "name": "Low Stock Item",
        "current_stock": 5.0,
        "minimum_stock": 10.0,
        "is_trackable": True
    }, headers=auth_headers)

    response = client.get("/api/v1/inventory/low-stock", headers=auth_headers)
    assert response.status_code == 200


def test_update_inventory_item(client, auth_headers):
    """Test updating inventory."""
    create_response = client.post("/api/v1/inventory/items", json={
        "name": "Rice",
        "current_stock": 100.0,
        "minimum_stock": 20.0,
        "is_trackable": True
    }, headers=auth_headers)
    assert create_response.status_code in (200, 201)
    item_id = create_response.json()["id"]

    response = client.put(f"/api/v1/inventory/items/{item_id}", json={
        "current_stock": 80.0
    }, headers=auth_headers)
    assert response.status_code == 200
