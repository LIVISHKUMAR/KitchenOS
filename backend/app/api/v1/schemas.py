"""Standardized API response schemas for consistent frontend consumption."""

from pydantic import BaseModel, Field
from typing import Optional, List, Any, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated API response."""
    success: bool = True
    data: List[T] = []
    total: int = 0
    page: int = 1
    page_size: int = 50
    has_next: bool = False
    has_prev: bool = False
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class MessageResponse(BaseModel):
    """Simple message response."""
    success: bool = True
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
