"""API documentation endpoints."""

from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/info")
async def api_info():
    """Get API information and capabilities."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Enterprise Restaurant Operating System API",
        "features": [
            "Multi-tenant architecture",
            "POS terminal management",
            "Kitchen Order Ticket (KOT) system",
            "Inventory management with auto-deduction",
            "Customer loyalty and wallet",
            "Dynamic pricing and promotions",
            "Franchise management",
            "Real-time WebSocket sync",
            "Offline sync with conflict resolution",
            "Aggregator integrations",
            "GST invoice generation",
            "Advanced analytics and reporting"
        ],
        "api_versions": ["v1"],
        "authentication": "Bearer JWT token",
        "rate_limits": {
            "default": "100 requests/minute",
            "auth": "5 requests/minute"
        },
        "endpoints": {
            "rest": "/api/v1/",
            "graphql": "/api/v1/graphql",
            "websocket": "/api/v1/ws",
            "health": "/health",
            "metrics": "/api/v1/metrics",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


@router.get("/endpoints")
async def list_endpoints():
    """List all available API endpoints."""
    return {
        "auth": {
            "POST /auth/token": "Login and get access token",
            "POST /auth/register": "Register new tenant",
            "POST /auth/refresh": "Refresh access token",
            "POST /auth/logout": "Logout"
        },
        "menu": {
            "GET /menu/categories": "List menu categories",
            "POST /menu/categories": "Create category",
            "GET /menu/items": "List menu items",
            "POST /menu/items": "Create menu item",
            "GET /menu/variants": "List item variants",
            "GET /menu/modifiers": "List item modifiers"
        },
        "orders": {
            "POST /orders/": "Create new order",
            "GET /orders/": "List orders",
            "GET /orders/{id}": "Get order details",
            "PUT /orders/{id}": "Update order",
            "PUT /orders/{id}/status": "Update order status",
            "DELETE /orders/{id}": "Cancel order"
        },
        "payments": {
            "POST /payments/": "Create payment",
            "GET /payments/": "List payments",
            "GET /payments/order/{id}": "Get payments for order"
        },
        "tables": {
            "GET /tables/": "List tables",
            "POST /tables/transfer": "Transfer table",
            "POST /tables/merge": "Merge tables"
        },
        "kot": {
            "GET /kot/": "Get KOT orders",
            "PUT /kot/items/{id}/status": "Update item prep status"
        },
        "inventory": {
            "GET /inventory/items": "List inventory items",
            "GET /inventory/low-stock": "Get low stock items"
        },
        "customers": {
            "GET /customers/": "List customers",
            "GET /customers/phone/{phone}": "Find by phone"
        },
        "reports": {
            "GET /reports/daily-sales": "Daily sales report",
            "GET /reports/item-wise-sales": "Item sales report",
            "GET /reports/category-wise-sales": "Category sales",
            "GET /reports/hourly-sales": "Hourly sales"
        },
        "analytics": {
            "GET /advanced-analytics/customer-lifetime-value": "CLV analysis",
            "GET /advanced-analytics/rfm-segmentation": "RFM segments",
            "GET /advanced-analytics/retention": "Retention metrics",
            "GET /demand/forecast": "Demand forecast"
        },
        "search": {
            "GET /search/?q={query}": "Full-text search",
            "GET /search/suggest?q={query}": "Search suggestions"
        }
    }


@router.get("/errors")
async def error_codes():
    """List API error codes."""
    return {
        "400": "Bad Request - Invalid input",
        "401": "Unauthorized - Invalid or missing token",
        "403": "Forbidden - Insufficient permissions",
        "404": "Not Found - Resource doesn't exist",
        "409": "Conflict - Resource already exists",
        "422": "Validation Error - Invalid data format",
        "429": "Too Many Requests - Rate limit exceeded",
        "500": "Internal Server Error",
        "503": "Service Unavailable"
    }
