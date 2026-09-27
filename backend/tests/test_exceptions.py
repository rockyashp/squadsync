"""
Tests for centralized exception handlers and consistent API response envelopes:
- 404 Route Not Found
- 422 Request Validation Failures
- Custom Domain Exceptions (NotFoundException, ConflictException, UnauthorizedException, ForbiddenException)
- ApiResponse helper methods
"""

import pytest
from httpx import AsyncClient

from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
)
from app.schemas.common import ApiResponse


def test_api_response_helpers():
    """Verify ApiResponse.ok and ApiResponse.fail factory methods."""
    ok_resp = ApiResponse.ok(data={"score": 100}, message="Done")
    assert ok_resp.success is True
    assert ok_resp.data == {"score": 100}
    assert ok_resp.message == "Done"
    assert ok_resp.errors is None

    fail_resp = ApiResponse.fail(message="Failed", errors=[{"field": "test", "message": "error"}])
    assert fail_resp.success is False
    assert fail_resp.data is None
    assert fail_resp.message == "Failed"
    assert len(fail_resp.errors) == 1


def test_custom_domain_exceptions():
    """Verify custom exception status codes and messages."""
    nf = NotFoundException("Item missing")
    assert nf.status_code == 404
    assert nf.message == "Item missing"

    cf = ConflictException("Duplicate key")
    assert cf.status_code == 409

    un = UnauthorizedException("Login required")
    assert un.status_code == 401

    fb = ForbiddenException("Access denied")
    assert fb.status_code == 403


@pytest.mark.asyncio
async def test_404_not_found_envelope(client: AsyncClient):
    """Verify non-existent route returns 404 with standardized ApiResponse envelope."""
    response = await client.get("/api/v1/non_existent_route_12345")
    assert response.status_code == 404

    data = response.json()
    assert data["success"] is False
    assert "data" in data
    assert data["data"] is None
    assert "errors" in data
    assert "does not exist" in data["message"].lower() or "not found" in data["message"].lower()


@pytest.mark.asyncio
async def test_422_validation_error_envelope(client: AsyncClient):
    """Verify input validation errors return 422 with structured field-level errors list."""
    # Send empty body to an endpoint requiring required fields
    response = await client.post("/api/v1/auth/register", json={})
    assert response.status_code == 422

    data = response.json()
    assert data["success"] is False
    assert data["data"] is None
    assert isinstance(data["errors"], list)
    assert len(data["errors"]) > 0

    # Verify each error item contains field, message, and type
    for err in data["errors"]:
        assert "field" in err
        assert "message" in err
        assert "type" in err
