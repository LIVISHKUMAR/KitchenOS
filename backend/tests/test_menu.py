"""Tests for menu endpoints."""

import pytest


def test_create_category(client, auth_headers):
    """Test creating a menu category."""
    response = client.post("/api/v1/menu/categories", json={
        "name": "Starters",
        "description": "Appetizers and starters",
        "display_order": 1
    }, headers=auth_headers)
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["name"] == "Starters"


def test_create_menu_item(client, auth_headers):
    """Test creating a menu item."""
    # Create category first
    cat_response = client.post("/api/v1/menu/categories", json={
        "name": "Mains",
        "display_order": 2
    }, headers=auth_headers)
    category_id = cat_response.json()["id"]

    # Create item
    response = client.post("/api/v1/menu/items", json={
        "name": "Butter Chicken",
        "description": "Creamy tomato curry with chicken",
        "base_price": 299.00,
        "is_veg": False,
        "category_id": category_id,
        "tax_rate": 5.0
    }, headers=auth_headers)
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["name"] == "Butter Chicken"
    assert float(data["base_price"]) == 299.00


def test_list_menu_items(client, auth_headers):
    """Test listing menu items."""
    # Create category
    cat_response = client.post("/api/v1/menu/categories", json={
        "name": "Drinks",
        "display_order": 3
    }, headers=auth_headers)
    category_id = cat_response.json()["id"]

    # Create items
    client.post("/api/v1/menu/items", json={
        "name": "Coke",
        "base_price": 60.00,
        "category_id": category_id
    }, headers=auth_headers)
    client.post("/api/v1/menu/items", json={
        "name": "Pepsi",
        "base_price": 60.00,
        "category_id": category_id
    }, headers=auth_headers)

    # List
    response = client.get("/api/v1/menu/items", headers=auth_headers)
    assert response.status_code in (200, 201)
    items = response.json()
    assert len(items) >= 2


def test_update_menu_item(client, auth_headers):
    """Test updating a menu item."""
    cat_response = client.post("/api/v1/menu/categories", json={
        "name": "Desserts"
    }, headers=auth_headers)
    category_id = cat_response.json()["id"]

    item_response = client.post("/api/v1/menu/items", json={
        "name": "Ice Cream",
        "base_price": 120.00,
        "category_id": category_id
    }, headers=auth_headers)
    item_id = item_response.json()["id"]

    # Update
    response = client.put(f"/api/v1/menu/items/{item_id}", json={
        "base_price": 150.00,
        "name": "Premium Ice Cream"
    }, headers=auth_headers)
    assert response.status_code in (200, 201)
    assert response.json()["name"] == "Premium Ice Cream"
    assert float(response.json()["base_price"]) == 150.00
