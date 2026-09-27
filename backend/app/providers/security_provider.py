"""
Security Provider encapsulating bcrypt password hashing and JWT token lifecycles.
"""

from datetime import datetime, timedelta, timezone
from typing import Any
import uuid

import bcrypt
import jwt

from app.constants import TokenTypes
from app.core.config import settings


class SecurityProvider:
    """
    Service provider for cryptographic operations: bcrypt password hashing and JWT encoding/decoding.
    """

    def __init__(
        self,
        secret_key: str = settings.SECRET_KEY,
        algorithm: str = settings.ALGORITHM,
        access_token_expire_minutes: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_token_expire_days: int = settings.REFRESH_TOKEN_EXPIRE_DAYS,
    ) -> None:
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days

    # --------------------------------------------------------------------------
    # Password Hashing (bcrypt)
    # --------------------------------------------------------------------------

    def hash_password(self, password: str) -> str:
        """
        Hash a plaintext password using bcrypt with standard salt rounds.
        Truncates strictly at 72 bytes UTF-8 to prevent DoS attacks.
        """
        password_bytes = password.encode("utf-8")[:72]
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plaintext password against a stored bcrypt hash in constant time.
        """
        password_bytes = plain_password.encode("utf-8")[:72]
        hashed_bytes = hashed_password.encode("utf-8")
        try:
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except (ValueError, TypeError):
            return False

    # --------------------------------------------------------------------------
    # JWT Token Operations
    # --------------------------------------------------------------------------

    def create_access_token(
        self,
        subject: str | Any,
        expires_delta: timedelta | None = None,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        """Create a signed JWT access token."""
        delta = expires_delta or timedelta(minutes=self.access_token_expire_minutes)
        return self._encode_jwt(
            subject=str(subject),
            token_type=TokenTypes.ACCESS.value,
            expires_delta=delta,
            extra_claims=extra_claims,
        )

    def create_refresh_token(
        self,
        subject: str | Any,
        expires_delta: timedelta | None = None,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        """Create a signed JWT refresh token."""
        delta = expires_delta or timedelta(days=self.refresh_token_expire_days)
        return self._encode_jwt(
            subject=str(subject),
            token_type=TokenTypes.REFRESH.value,
            expires_delta=delta,
            extra_claims=extra_claims,
        )

    def create_password_reset_token(
        self,
        subject: str | Any,
        expires_delta: timedelta | None = None,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        """Create a signed JWT password reset token (valid for 15 minutes by default)."""
        delta = expires_delta or timedelta(minutes=15)
        return self._encode_jwt(
            subject=str(subject),
            token_type=TokenTypes.PASSWORD_RESET.value,
            expires_delta=delta,
            extra_claims=extra_claims,
        )

    def decode_token(self, token: str) -> dict[str, Any]:
        """
        Decode and cryptographically verify a JWT signature and standard claims.
        Raises jwt.PyJWTError on expiration or invalid signature.
        """
        return jwt.decode(
            token,
            self.secret_key,
            algorithms=[self.algorithm],
        )

    def _encode_jwt(
        self,
        subject: str,
        token_type: str,
        expires_delta: timedelta,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        now = datetime.now(timezone.utc)
        expire = now + expires_delta

        payload: dict[str, Any] = {
            "jti": str(uuid.uuid4()),
            "sub": subject,
            "type": token_type,
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
        }

        if extra_claims:
            payload.update(extra_claims)

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)


# Default security provider singleton
security_provider = SecurityProvider()
