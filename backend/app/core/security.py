"""
Security utilities for password hashing and JWT lifecycle management.
Delegates to SecurityProvider for architectural consistency.
"""

from datetime import timedelta
from typing import Any

from app.providers.security_provider import security_provider


def get_password_hash(password: str) -> str:
    """Hashes plaintext password using bcrypt."""
    return security_provider.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plaintext password against stored bcrypt hash."""
    return security_provider.verify_password(plain_password, hashed_password)


def create_access_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Creates a signed JWT access token."""
    return security_provider.create_access_token(
        subject=subject,
        expires_delta=expires_delta,
        extra_claims=extra_claims,
    )


def create_refresh_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Creates a signed JWT refresh token."""
    return security_provider.create_refresh_token(
        subject=subject,
        expires_delta=expires_delta,
        extra_claims=extra_claims,
    )


def create_password_reset_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Creates a signed JWT password reset token."""
    return security_provider.create_password_reset_token(
        subject=subject,
        expires_delta=expires_delta,
        extra_claims=extra_claims,
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decodes and validates a signed JWT token."""
    return security_provider.decode_token(token)
