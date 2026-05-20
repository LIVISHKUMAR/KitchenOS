"""Cursor-based pagination utilities for list endpoints."""

from pydantic import BaseModel
from typing import Optional, List, TypeVar, Generic
from sqlalchemy.orm import Query

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination request parameters."""
    cursor: Optional[str] = None
    limit: int = 50


class PaginatedResult(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    data: List[T]
    total: int
    has_next: bool
    has_prev: bool
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None


def paginate_query(
    query: Query,
    limit: int = 50,
    cursor: Optional[str] = None,
    cursor_column=None,
) -> dict:
    """Apply cursor-based pagination to a SQLAlchemy query.

    Args:
        query: The SQLAlchemy query to paginate
        limit: Maximum number of results (max 100)
        cursor: Cursor value for next page
        cursor_column: The column to use for cursor (e.g., Order.created_at)

    Returns:
        Dict with data, total, has_next, has_prev, next_cursor, prev_cursor
    """
    # Cap limit at 100
    limit = min(limit, 100)

    # Get total count
    total = query.count()

    # Apply cursor if provided
    if cursor and cursor_column is not None:
        query = query.filter(cursor_column > cursor)

    # Fetch one extra to check if there's a next page
    items = query.order_by(cursor_column).limit(limit + 1).all()

    has_next = len(items) > limit
    if has_next:
        items = items[:limit]

    # Get cursor values
    next_cursor = None
    prev_cursor = None

    if items and has_next:
        last_item = items[-1]
        next_cursor = str(getattr(last_item, cursor_column.key if hasattr(cursor_column, 'key') else 'id'))

    if items and cursor:
        first_item = items[0]
        prev_cursor = str(getattr(first_item, cursor_column.key if hasattr(cursor_column, 'key') else 'id'))

    return {
        "data": items,
        "total": total,
        "has_next": has_next,
        "has_prev": cursor is not None,
        "next_cursor": next_cursor,
        "prev_cursor": prev_cursor,
    }


def simple_paginate(
    query: Query,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """Apply offset-based pagination (simpler alternative).

    Args:
        query: The SQLAlchemy query to paginate
        page: Page number (1-indexed)
        page_size: Items per page (max 100)

    Returns:
        Dict with data, total, page, page_size, has_next, has_prev
    """
    page_size = min(page_size, 100)
    page = max(1, page)

    total = query.count()
    offset = (page - 1) * page_size

    items = query.offset(offset).limit(page_size + 1).all()
    has_next = len(items) > page_size
    if has_next:
        items = items[:page_size]

    return {
        "data": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": has_next,
        "has_prev": page > 1,
    }
