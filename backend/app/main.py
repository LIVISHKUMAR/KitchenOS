from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from app.api.health import router as health_router
from app.api.middleware.security import SecurityHeadersMiddleware

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    description="""
    KitchenOS — Enterprise Restaurant Operating System API

    Multi-tenant restaurant management platform with POS, KOT, inventory,
    payments, loyalty, reporting, and aggregator integrations.
    """,
    openapi_tags=[
        {"name": "auth", "description": "Authentication & registration"},
        {"name": "tenants", "description": "Tenant management"},
        {"name": "branches", "description": "Branch management"},
        {"name": "users", "description": "User management"},
        {"name": "menu", "description": "Menu categories, items, variants, modifiers"},
        {"name": "orders", "description": "Order management"},
        {"name": "payments", "description": "Payment processing"},
        {"name": "inventory", "description": "Inventory & stock management"},
        {"name": "customers", "description": "Customer profiles"},
        {"name": "tables", "description": "Table management & transfers"},
        {"name": "reports", "description": "Sales & analytics reports"},
        {"name": "tax", "description": "Tax configuration"},
        {"name": "kot", "description": "Kitchen Order Tickets"},
        {"name": "coupons", "description": "Discount coupons"},
        {"name": "split-billing", "description": "Split bill management"},
        {"name": "audit", "description": "Audit trail"},
        {"name": "loyalty", "description": "Loyalty points"},
        {"name": "recipes", "description": "Recipe mapping & food cost"},
        {"name": "vendors", "description": "Vendor management"},
        {"name": "shifts", "description": "Shift & attendance"},
        {"name": "purchase-orders", "description": "Purchase order workflow"},
        {"name": "aggregator", "description": "Aggregator integrations"},
        {"name": "invoices", "description": "GST invoice generation"},
    ]
)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Request validation middleware
from app.api.middleware.validation import RequestValidationMiddleware
app.add_middleware(RequestValidationMiddleware)

# Response compression (enable in production)
if not settings.DEBUG:
    from app.api.middleware.compression import CompressionMiddleware
    app.add_middleware(CompressionMiddleware)

# Rate limiting middleware (enable in production)
if not settings.DEBUG:
    from app.api.middleware.rate_limit import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3004", "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(api_router, prefix="/api/v1")
app.include_router(health_router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to KitchenOS API",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else None
    }
