"""Tests for authentication endpoints."""

import pytest


def test_register(client):
    """Test tenant registration."""
    response = client.post("/api/v1/auth/register", json={
        "name": "New Restaurant",
        "email": "new@restaurant.com",
        "password": "securepass123",
        "phone": "9876543210"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["tenant"]["name"] == "New Restaurant"
    assert data["user"]["role"] == "admin"


def test_register_duplicate_email(client):
    """Test registration with duplicate email."""
    client.post("/api/v1/auth/register", json={
        "name": "Restaurant 1",
        "email": "dup@restaurant.com",
        "password": "securepass123"
    })
    response = client.post("/api/v1/auth/register", json={
        "name": "Restaurant 2",
        "email": "dup@restaurant.com",
        "password": "securepass123"
    })
    assert response.status_code == 409


def test_login(client):
    """Test login with valid credentials."""
    # Register first
    client.post("/api/v1/auth/register", json={
        "name": "Login Test",
        "email": "login@test.com",
        "password": "testpass123"
    })

    # Login
    response = client.post("/api/v1/auth/token", data={
        "username": "login@test.com",
        "password": "testpass123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client):
    """Test login with invalid password."""
    client.post("/api/v1/auth/register", json={
        "name": "Bad Pass Test",
        "email": "badpass@test.com",
        "password": "correctpass"
    })

    response = client.post("/api/v1/auth/token", data={
        "username": "badpass@test.com",
        "password": "wrongpass"
    })
    assert response.status_code == 401


def test_refresh_token(client):
    """Test token refresh."""
    # Register
    reg_response = client.post("/api/v1/auth/register", json={
        "name": "Refresh Test",
        "email": "refresh@test.com",
        "password": "testpass123"
    })
    refresh_token = reg_response.json()["refresh_token"]

    # Refresh
    response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_protected_endpoint_without_token(client):
    """Test accessing protected endpoint without token."""
    response = client.get("/api/v1/orders/")
    assert response.status_code == 403  # No Authorization header


def test_protected_endpoint_with_token(client, auth_headers):
    """Test accessing protected endpoint with valid token."""
    response = client.get("/api/v1/orders/", headers=auth_headers)
    assert response.status_code == 200
