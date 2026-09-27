"""
Reusable common Pydantic response models enforcing a consistent API response structure:
{
    "success": bool,
    "message": str,
    "data": Any | None,
    "errors": Any | None
}
"""

from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ValidationErrorItem(BaseModel):
    """Detailed representation of an individual input validation failure."""
    field: str = Field(..., description="Dot-separated path to invalid parameter or payload field")
    message: str = Field(..., description="Human-readable explanation of the validation constraint failure")
    type: str = Field(..., description="Validation error code/type identifier")


class ApiResponse(BaseModel, Generic[T]):
    """
    Unified API response envelope across the entire SquadSync backend.
    Ensures frontend clients receive a deterministic contract for both successes and errors.
    """
    success: bool = Field(..., description="Flag indicating if the operation succeeded")
    message: str = Field(..., description="High-level status or error summary message")
    data: T | None = Field(default=None, description="Typed payload returned upon success")
    errors: Any | None = Field(default=None, description="Validation failure list or error details upon failure")

    @classmethod
    def ok(cls, data: T | None = None, message: str = "Operation completed successfully.") -> "ApiResponse[T]":
        """Factory for successful API responses."""
        return cls(success=True, message=message, data=data, errors=None)

    @classmethod
    def fail(cls, message: str, errors: Any | None = None) -> "ApiResponse[None]":
        """Factory for failure API responses."""
        return cls(success=False, message=message, data=None, errors=errors)


class MessageResponse(BaseModel):
    """Standard generic message payload."""
    message: str


class ErrorResponse(BaseModel):
    """Standardized error response model."""
    detail: str


class PaginatedData(BaseModel, Generic[T]):
    """Pagination metadata container."""
    items: list[T]
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    size: int = Field(..., ge=1, description="Page size limit")
    pages: int = Field(..., ge=0, description="Total calculated pages")


class PaginatedResponse(ApiResponse[PaginatedData[T]], Generic[T]):
    """Paginated response wrapped in standard ApiResponse envelope."""
    pass
