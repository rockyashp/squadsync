"""
Centralized exception handling and custom application exceptions.
Standardizes all error responses into the consistent ApiResponse format:
{
    "success": false,
    "message": str,
    "data": null,
    "errors": Any | null
}
"""

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import jwt
from pydantic import ValidationError
from sqlalchemy.exc import DBAPIError, IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings

HTTP_422 = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)

logger = logging.getLogger(__name__)


# ==============================================================================
# Custom Domain Exceptions
# ==============================================================================

class AppException(Exception):
    """Base application exception for domain errors."""

    def __init__(
        self,
        message: str = "An application error occurred.",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        errors: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.errors = errors


class NotFoundException(AppException):
    """Raised when an entity or resource is not found."""

    def __init__(self, message: str = "The requested resource was not found.") -> None:
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND)


class ConflictException(AppException):
    """Raised when an operation conflicts with existing resources."""

    def __init__(self, message: str = "A conflict occurred with an existing resource.") -> None:
        super().__init__(message=message, status_code=status.HTTP_409_CONFLICT)


class UnauthorizedException(AppException):
    """Raised when authentication credentials are required or invalid."""

    def __init__(self, message: str = "Authentication required or invalid credentials.") -> None:
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(AppException):
    """Raised when authenticated user lacks permission."""

    def __init__(self, message: str = "You do not have permission to access this resource.") -> None:
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN)


class ValidationException(AppException):
    """Raised when domain validation fails."""

    def __init__(self, message: str = "Validation failed for the request.", errors: Any | None = None) -> None:
        super().__init__(message=message, status_code=HTTP_422, errors=errors)


# Common domain aliases
EntityNotFoundException = NotFoundException
AuthenticationException = UnauthorizedException


# ==============================================================================
# Helper to Format Validation Errors
# ==============================================================================

def format_pydantic_validation_errors(errors: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Transforms Pydantic / FastAPI validation error dictionaries into clean client payloads."""
    formatted = []
    for err in errors:
        loc = err.get("loc", [])
        # Strip internal 'body', 'query', etc. if leading
        field_parts = [str(part) for part in loc if part not in ("body", "query", "path")]
        field_name = ".".join(field_parts) if field_parts else "request"

        formatted.append({
            "field": field_name,
            "message": err.get("msg", "Invalid input value."),
            "type": err.get("type", "value_error"),
        })
    return formatted


# ==============================================================================
# Centralized Exception Handlers Registration
# ==============================================================================

def register_exception_handlers(app: FastAPI) -> None:
    """Registers all global exception handlers to enforce uniform API response envelopes."""

    @app.exception_handler(AppException)
    async def handle_app_exception(_: Request, exc: AppException) -> JSONResponse:
        """Handles all custom application domain exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.message,
                "data": None,
                "errors": exc.errors,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        """Handles Pydantic input validation failures (422 Unprocessable Entity)."""
        formatted_errors = format_pydantic_validation_errors(exc.errors())
        return JSONResponse(
            status_code=HTTP_422,
            content={
                "success": False,
                "message": "Input validation failed. Please check the 'errors' field for details.",
                "data": None,
                "errors": formatted_errors,
            },
        )

    @app.exception_handler(ValidationError)
    async def handle_pydantic_validation_error(_: Request, exc: ValidationError) -> JSONResponse:
        """Handles direct Pydantic model validation errors."""
        formatted_errors = format_pydantic_validation_errors(exc.errors())
        return JSONResponse(
            status_code=HTTP_422,
            content={
                "success": False,
                "message": "Model validation failed.",
                "data": None,
                "errors": formatted_errors,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_starlette_http_exception(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handles Starlette / FastAPI HTTPExceptions including 404 and 405."""
        message = str(exc.detail) if exc.detail else "An HTTP error occurred."
        if exc.status_code == status.HTTP_404_NOT_FOUND and message == "Not Found":
            message = "The requested resource or endpoint does not exist."

        headers = getattr(exc, "headers", None)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": message,
                "data": None,
                "errors": None,
            },
            headers=headers,
        )

    @app.exception_handler(jwt.ExpiredSignatureError)
    async def handle_jwt_expired(_: Request, __: jwt.ExpiredSignatureError) -> JSONResponse:
        """Handles expired JWT authentication tokens (401 Unauthorized)."""
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "message": "Authentication token has expired. Please log in again.",
                "data": None,
                "errors": None,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(jwt.PyJWTError)
    async def handle_jwt_error(_: Request, __: jwt.PyJWTError) -> JSONResponse:
        """Handles malformed or invalid JWT tokens (401 Unauthorized)."""
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "message": "Invalid authentication credentials.",
                "data": None,
                "errors": None,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(IntegrityError)
    async def handle_integrity_error(_: Request, exc: IntegrityError) -> JSONResponse:
        """Handles database constraint violations (e.g. unique keys, foreign keys)."""
        logger.warning("Database integrity constraint violated: %s", str(exc.orig))
        message = "A database constraint violation occurred. A duplicate value may already exist."
        orig_msg = str(exc.orig).lower() if exc.orig else ""

        if "unique" in orig_msg or "duplicate" in orig_msg:
            message = "An entity with one of these unique values already exists."
        elif "foreign key" in orig_msg:
            message = "Referenced entity does not exist."

        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "success": False,
                "message": message,
                "data": None,
                "errors": str(exc.orig) if settings.DEBUG else None,
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def handle_sqlalchemy_error(_: Request, exc: SQLAlchemyError) -> JSONResponse:
        """Handles general database failures (500 Internal Server Error)."""
        logger.error("Database error occurred: %s", str(exc), exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "A database error occurred while processing your request.",
                "data": None,
                "errors": str(exc) if settings.DEBUG else None,
            },
        )

    @app.exception_handler(Exception)
    async def handle_unhandled_exception(_: Request, exc: Exception) -> JSONResponse:
        """Catch-all handler for unexpected server errors (500 Internal Server Error)."""
        logger.critical("Unhandled server exception: %s", str(exc), exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "An unexpected internal server error occurred. Please try again later.",
                "data": None,
                "errors": [str(exc)] if settings.DEBUG else None,
            },
        )
