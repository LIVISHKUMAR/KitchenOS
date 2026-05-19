"""Tests for payment endpoints."""

import pytest


def _create_order(client, auth_headers):
    """Helper to create an order."""
    cat = client.post("/api/v1/menu/categories", json={"name": "Test"}, headers=auth_headers)
    item = client.post("/api/v1/menu/items", json={
        "name": "Test Item",
        "base_price": 200.00,
        "category_id": cat.json()["id"]
    }, headers=auth_headers)
    order = client.post("/api/v1/orders/", json={
        "order_type": "dine_in",
        "items": [{
            "menu_item_id": item.json()["id"],
            "item_name": "Test Item",
            "quantity": 1,
            "unit_price": 200.00
        }]
    }, headers=auth_headers)
    return order.json()


def test_create_payment(client, auth_headers):
    """Test creating a payment."""
    order = _create_order(client, auth_headers)

    response = client.post("/api/v1/payments/", json={
        "order_id": order["id"],
        "amount": float(order["total"]),
        "payment_method": "cash",
        "idempotency_key": "test-payment-001"
    }, headers=auth_headers)

    assert response.status_code in (200, 201)
    data = response.json()
    assert data["payment_method"] == "cash"
    assert float(data["amount"]) == float(order["total"])


def test_get_payments_by_order(client, auth_headers):
    """Test getting payments for an order."""
    order = _create_order(client, auth_headers)

    client.post("/api/v1/payments/", json={
        "order_id": order["id"],
        "amount": float(order["total"]),
        "payment_method": "card",
        "idempotency_key": "test-payment-002"
    }, headers=auth_headers)

    response = client.get(f"/api/v1/payments/order/{order['id']}", headers=auth_headers)
    assert response.status_code == 200
    payments = response.json()
    assert len(payments) >= 1
