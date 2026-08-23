"""
RecoverAI — Common & Pagination Schemas
=======================================
Defines reusable generic models for paginated collections, request IDs, and error envelopes.
"""

from __future__ import annotations

from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    total: int = Field(..., ge=0, description="Total count of items matching filters")
    total_pages: int = Field(..., ge=0, description="Total available pages")


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(use_enum_values=True)

    items: List[T] = Field(default_factory=list, description="List of items for current page")
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=0)


class ErrorDetail(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    code: str = Field(..., description="Machine-readable error identifier")
    message: str = Field(..., description="Human-readable error explanation")
    request_id: Optional[str] = Field(None, description="Unique correlation ID")
    details: Optional[Any] = Field(None, description="Detailed validation breakdown")


class ErrorResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    error: ErrorDetail


class SuccessResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(use_enum_values=True)

    data: T
    message: Optional[str] = None
