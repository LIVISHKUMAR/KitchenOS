"""Test fixtures for KitchenOS test suite."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.infrastructure.database import Base, get_db_session
from app.core.config import settings

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db_session] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    """Get a test database session."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    """Get a test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Register a tenant and return auth headers."""
    # Register
    response = client.post("/api/v1/auth/register", json={
        "name": "Test Restaurant",
        "email": "test@restaurant.com",
        "password": "testpassword123",
        "phone": "9876543210"
    })

    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
    else:
        # Login if already exists
        response = client.post("/api/v1/auth/token", data={
            "username": "test@restaurant.com",
            "password": "testpassword123"
        })
        data = response.json()
        token = data.get("access_token")

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def tenant_id(auth_headers, client):
    """Get the tenant_id from the current user."""
    # Decode from token or use a fixed value
    return "test-tenant-id"
