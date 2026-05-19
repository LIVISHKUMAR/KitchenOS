"""Role-Based Access Control (RBAC) with granular permissions."""

from typing import List, Set
from functools import wraps

# Permission definitions: resource:action
PERMISSIONS = {
    "admin": [
        # Full access to everything
        "tenant:*", "branch:*", "user:*", "menu:*",
        "order:*", "payment:*", "inventory:*", "customer:*",
        "report:*", "settings:*", "audit:*", "coupon:*",
        "table:*", "kot:*", "tax:*", "vendor:*",
        "purchase_order:*", "shift:*", "loyalty:*",
        "aggregator:*", "recipe:*"
    ],
    "manager": [
        # Branch operations
        "branch:read",
        "user:read", "user:create", "user:update",
        "menu:*",
        "order:*", "payment:*",
        "inventory:*", "customer:*",
        "report:read",
        "coupon:*", "table:*", "kot:*",
        "tax:read", "vendor:*", "purchase_order:*",
        "shift:*", "loyalty:read",
        "recipe:*"
    ],
    "cashier": [
        "menu:read",
        "order:create", "order:read", "order:update",
        "payment:create", "payment:read",
        "customer:read", "customer:create", "customer:update",
        "table:read", "kot:read",
        "coupon:read", "loyalty:read"
    ],
    "chef": [
        "menu:read",
        "order:read", "order:update",
        "kot:read", "kot:update",
        "inventory:read"
    ],
    "waiter": [
        "menu:read",
        "order:create", "order:read", "order:update",
        "customer:read", "customer:create",
        "table:read", "kot:read"
    ]
}


def expand_permissions(role_permissions: List[str]) -> Set[str]:
    """Expand wildcard permissions (e.g., 'menu:*' → 'menu:read', 'menu:create', etc.)."""
    expanded = set()
    all_actions = ["read", "create", "update", "delete", "export"]

    for perm in role_permissions:
        resource, action = perm.split(":")
        if action == "*":
            for a in all_actions:
                expanded.add(f"{resource}:{a}")
        else:
            expanded.add(perm)

    return expanded


def get_role_permissions(role: str) -> Set[str]:
    """Get all permissions for a role."""
    role_perms = PERMISSIONS.get(role, [])
    return expand_permissions(role_perms)


def has_permission(role: str, permission: str) -> bool:
    """Check if a role has a specific permission.

    Args:
        role: User role (admin, manager, cashier, chef, waiter)
        permission: Permission string in format "resource:action" (e.g., "menu:read")
    """
    if role == "admin":
        return True  # Admin has all permissions

    perms = get_role_permissions(role)
    return permission in perms


def require_permission(permission: str):
    """Decorator/dependency factory for endpoint permission checking.

    Usage:
        @router.get("/menu")
        async def list_menu(current_user: dict = Depends(require_permission("menu:read"))):
            ...
    """
    from fastapi import Depends, HTTPException, status
    from app.api.dependencies import get_current_user

    async def permission_checker(current_user: dict = Depends(get_current_user)):
        role = current_user.get("role", "")
        if not has_permission(role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required: {permission}"
            )
        return current_user

    return permission_checker


def check_branch_access(user_branch_id: str, resource_branch_id: str, role: str) -> bool:
    """Check if user has access to a resource based on branch.

    Admin/Manager can access all branches.
    Other roles can only access their own branch.
    """
    if role in ("admin", "manager"):
        return True
    return user_branch_id == resource_branch_id
