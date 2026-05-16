from fastapi import APIRouter

api_router = APIRouter()

# Import and include routers from each module
from app.api.v1.endpoints import auth, tenants, branches, users, menu, orders, payments, inventory, customers

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(branches.router, prefix="/branches", tags=["branches"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(menu.router, prefix="/menu", tags=["menu"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
