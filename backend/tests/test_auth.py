"""
Unit and integration tests for Authentication and Security primitives:
- Password hashing and verification with bcrypt
- JWT token generation, claims, and decoding
- Strong password policy enforcement
- Auth endpoints and error handling
"""

from datetime import timedelta
import pytest
from httpx import AsyncClient
import jwt

from app.config import settings
from app.constants import TokenTypes
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.schemas.auth import UserRegisterRequest


def test_password_hashing_and_verification():
    """Verify bcrypt hashing generates non-reversible hashes and verifies correctly."""
    plain = "S3cureP@ssword2026!"
    hashed = get_password_hash(plain)

    assert hashed != plain
    assert hashed.startswith("$2")  # Standard bcrypt prefix
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_jwt_access_and_refresh_token_lifecycle():
    """Verify JWT access and refresh token encoding, claims, and decoding."""
    subject = "user-12345"

    access_token = create_access_token(subject=subject, expires_delta=timedelta(minutes=15))
    payload = decode_token(access_token)

    assert payload["sub"] == subject
    assert payload["type"] == TokenTypes.ACCESS.value
    assert "exp" in payload
    assert "iat" in payload

    refresh_token = create_refresh_token(subject=subject, expires_delta=timedelta(days=7))
    refresh_payload = decode_token(refresh_token)

    assert refresh_payload["sub"] == subject
    assert refresh_payload["type"] == TokenTypes.REFRESH.value


def test_jwt_expired_token():
    """Verify expired token raises ExpiredSignatureError."""
    subject = "user-expired"
    token = create_access_token(subject=subject, expires_delta=timedelta(seconds=-10))

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token)


@pytest.mark.parametrize(
    "invalid_password, expected_error",
    [
        ("short1!", "at least 8 characters"),
        ("nouppercase123!", "uppercase letter"),
        ("NOLOWERCASE123!", "lowercase letter"),
        ("NoDigitsHere!!", "digit"),
        ("NoSpecialChar123", "special character"),
    ],
)
def test_strong_password_validation_rejections(invalid_password: str, expected_error: str):
    """Verify strong password policy rejects passwords lacking complexity."""
    with pytest.raises(ValueError) as exc_info:
        UserRegisterRequest(
            username="valid_user",
            email="user@squadsync.gg",
            password=invalid_password,
        )
    assert expected_error in str(exc_info.value)


@pytest.mark.asyncio
async def test_register_weak_password_api_error_envelope(client: AsyncClient):
    """Test POST /api/v1/auth/register returns 422 with standardized error response."""
    payload = {
        "username": "gamer123",
        "email": "gamer@squadsync.gg",
        "password": "weak",  # Fails length and complexity
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422

    data = response.json()
    assert data["success"] is False
    assert "validation" in data["message"].lower()
    assert isinstance(data["errors"], list)
    assert any(err.get("field") == "password" for err in data["errors"])


@pytest.mark.asyncio
async def test_login_validation_missing_password(client: AsyncClient):
    """Test POST /api/v1/auth/login returns 422 when password is missing."""
    payload = {"username_or_email": "gamer123"}
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 422

    data = response.json()
    assert data["success"] is False
    assert any(err.get("field") == "password" for err in data["errors"])


@pytest.mark.asyncio
async def test_refresh_token_invalid_signature(client: AsyncClient):
    """Test POST /api/v1/auth/refresh returns 401 when token is invalid."""
    payload = {"refresh_token": "invalid.jwt.token.string"}
    response = await client.post("/api/v1/auth/refresh", json=payload)
    assert response.status_code == 401

    data = response.json()
    assert data["success"] is False


@pytest.mark.asyncio
async def test_get_current_user_me_unauthenticated(client: AsyncClient):
    """Test GET /api/v1/auth/me returns 401 Unauthorized without Authorization header."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401

    data = response.json()
    assert data["success"] is False
    assert "token" in data["message"].lower() or "authenticated" in data["message"].lower() or "credentials" in data["message"].lower()


@pytest.mark.asyncio
async def test_get_current_user_me_authenticated(authenticated_client: AsyncClient):
    """Test GET /api/v1/auth/me returns user details in ApiResponse envelope when authenticated."""
    response = await authenticated_client.get("/api/v1/auth/me")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["data"]["username"] == "pro_tester"
    assert data["data"]["email"] == "tester@squadsync.gg"


@pytest.mark.asyncio
async def test_forgot_password_generic_response(client: AsyncClient):
    """Test POST /api/v1/auth/forgot-password returns generic 200 OK message."""
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nonexistent@squadsync.gg"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "reset link" in data["message"].lower()


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client: AsyncClient):
    """Test POST /api/v1/auth/reset-password rejects malformed token with 400 Bad Request."""
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": "malformed.invalid.token",
            "new_password": "N3wStrongPassword123!",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "token" in data["message"].lower()
