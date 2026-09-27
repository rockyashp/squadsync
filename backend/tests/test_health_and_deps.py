"""
Tests for Health check endpoints, dependency injection logic, and centralized exception handling.
"""

from datetime import datetime, timedelta, timezone
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException, status
import httpx
from httpx import ASGITransport, AsyncClient
import jwt
import pytest

from app.config import settings
from app.constants import TokenTypes
from app.core.dependencies import (
    get_current_active_user,
    get_current_user,
    get_db,
)
from app.core.security import create_access_token, create_refresh_token
from app.main import app
from app.models.user import User
from app.services.user_service import UserService


@pytest.mark.asyncio
async def test_health_check_healthy(client: AsyncClient):
    """Test GET /health returns 200 and healthy status."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "status" in data["data"]
    assert data["data"]["app_name"] == settings.APP_NAME


@pytest.mark.asyncio
async def test_health_check_degraded_on_db_failure():
    """Test GET /health returns degraded status when database query fails."""
    mock_db = AsyncMock()
    mock_db.execute.side_effect = Exception("DB Connection Lost")

    async def override_failing_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_failing_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "degraded"
        assert data["data"]["database"]["status"] == "disconnected"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_current_user_valid():
    """Test get_current_user returns User for valid access token."""
    user_id = uuid.uuid4()
    token = create_access_token(subject=str(user_id))
    now = datetime.now(timezone.utc)
    mock_user = User(
        id=user_id,
        username="valid_user",
        email="valid@squadsync.gg",
        password_hash="fakehash",
        is_active=True,
        is_locked=False,
        failed_login_attempts=0,
        created_at=now,
        updated_at=now,
    )

    mock_user_service = AsyncMock(spec=UserService)
    mock_user_service.get_by_id.return_value = mock_user

    result = await get_current_user(token=token, user_service=mock_user_service)
    assert result.id == user_id
    assert result.username == "valid_user"


@pytest.mark.asyncio
async def test_get_current_user_expired_token():
    """Test get_current_user raises 401 when token has expired."""
    user_id = uuid.uuid4()
    expired_token = create_access_token(
        subject=str(user_id),
        expires_delta=timedelta(minutes=-5),
    )

    mock_user_service = AsyncMock(spec=UserService)
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token=expired_token, user_service=mock_user_service)
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_get_current_user_wrong_token_type():
    """Test get_current_user raises 401 when refresh token is provided instead of access token."""
    user_id = uuid.uuid4()
    refresh_tok = create_refresh_token(subject=str(user_id))
    mock_user_service = AsyncMock(spec=UserService)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token=refresh_tok, user_service=mock_user_service)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_user_not_found():
    """Test get_current_user raises 401 when token subject UUID does not exist in DB."""
    user_id = uuid.uuid4()
    token = create_access_token(subject=str(user_id))
    mock_user_service = AsyncMock(spec=UserService)
    mock_user_service.get_by_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token=token, user_service=mock_user_service)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_active_user_inactive():
    """Test get_current_active_user raises 403 when user is deactivated."""
    now = datetime.now(timezone.utc)
    inactive_user = User(
        id=uuid.uuid4(),
        username="inactive_player",
        email="inactive@squadsync.gg",
        password_hash="fakehash",
        is_active=False,
        is_locked=False,
        failed_login_attempts=0,
        created_at=now,
        updated_at=now,
    )
    with pytest.raises(HTTPException) as exc_info:
        await get_current_active_user(current_user=inactive_user)
    assert exc_info.value.status_code == 403
    assert "inactive" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_get_current_active_user_locked():
    """Test get_current_active_user raises 403 when user account is locked."""
    now = datetime.now(timezone.utc)
    locked_user = User(
        id=uuid.uuid4(),
        username="locked_player",
        email="locked@squadsync.gg",
        password_hash="fakehash",
        is_active=True,
        is_locked=True,
        failed_login_attempts=5,
        created_at=now,
        updated_at=now,
    )
    with pytest.raises(HTTPException) as exc_info:
        await get_current_active_user(current_user=locked_user)
    assert exc_info.value.status_code == 403
    assert "locked" in exc_info.value.detail.lower()
