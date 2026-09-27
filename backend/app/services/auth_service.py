"""
Authentication service orchestrating registration, credential verification, and token issuance.
"""

from typing import Any
import uuid

from fastapi import HTTPException, status
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.constants import TokenTypes
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.services.base import BaseService
from app.services.user_service import UserService


class AuthService(BaseService[Any]):
    """High-level authentication service encapsulating auth rules, hashing, and token lifecycles."""

    def __init__(
        self,
        db: AsyncSession,
        user_service: UserService | None = None,
    ) -> None:
        super().__init__(db)
        self.user_service = user_service or UserService(db)

    async def register(self, register_in: UserRegisterRequest) -> User:
        """
        Registers a new user with unique username, unique email, and hashed password.
        Raises 409 Conflict if username or email already exists.
        """
        # Validate uniqueness of email
        existing_email = await self.user_service.get_by_email(register_in.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email address already exists.",
            )

        # Validate uniqueness of username
        existing_user = await self.user_service.get_by_username(register_in.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This username is already taken. Please choose a different one.",
            )

        # Secure password with bcrypt
        password_hash = get_password_hash(register_in.password)

        # Persist user
        user = await self.user_service.create_user(
            username=register_in.username,
            email=register_in.email,
            password_hash=password_hash,
        )
        return user

    async def login(self, login_in: UserLoginRequest) -> TokenResponse:
        """
        Authenticates user credentials, tracks failed login attempts, and locks account after 5 failures.
        """
        user = await self.user_service.get_by_username_or_email(login_in.username_or_email)

        if not user:
            # Constant-time dummy verification to mitigate timing attacks / username enumeration
            verify_password("dummy_password_timing_mitigation", "$2b$12$e8Y7z7r3Wv1yW0Qn0qO4teP0q.2tQ4c.5k8v8v8v8v8v8v8v8v8v8")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if account is locked
        if user.is_locked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is locked due to multiple failed login attempts. Please contact support.",
            )

        # Check if account is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated. Please contact support.",
            )

        # Verify password hash
        if not verify_password(login_in.password, user.password_hash):
            attempts = await self.user_service.record_failed_attempt(user, max_attempts=5)
            if attempts >= 5:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account has been locked due to 5 consecutive failed login attempts.",
                )
            remaining = 5 - attempts
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid credentials. {remaining} attempt(s) remaining before account lockout.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Reset failed attempts counter upon successful verification
        await self.user_service.reset_failed_attempts(user)

        # Issue JWT access & refresh tokens
        return self._generate_token_response(user.id)

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """
        Validates a JWT refresh token and issues a fresh token pair.
        """
        try:
            payload = decode_token(refresh_token)
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except (jwt.PyJWTError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Ensure the token provided is explicitly a refresh token
        if payload.get("type") != TokenTypes.REFRESH.value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Expected a refresh token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token subject missing.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            user_uuid = uuid.UUID(user_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Malformed token subject identifier.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = await self.user_service.get_by_id(user_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User associated with this token no longer exists.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if user.is_locked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is locked.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive.",
            )

        return self._generate_token_response(user.id)

    def _generate_token_response(self, user_id: uuid.UUID) -> TokenResponse:
        """Helper to create access and refresh tokens for a user ID."""
        access_token = create_access_token(subject=str(user_id))
        refresh_token = create_refresh_token(subject=str(user_id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def forgot_password(self, request: ForgotPasswordRequest) -> ForgotPasswordResponse:
        """
        Initiates password reset sequence. If email is registered and active,
        generates a signed 15-minute JWT reset token.
        Always returns generic confirmation message to eliminate user enumeration side-channels.
        """
        user = await self.user_service.get_by_email(request.email)
        reset_token = None

        if user and user.is_active:
            reset_token = create_password_reset_token(subject=str(user.id))
            # In production, dispatch email with reset link: https://app.squadsync.gg/reset-password?token=...
            # In development/testing, optionally expose reset_token for verification

        return ForgotPasswordResponse(
            message="If the email is registered, a password reset link has been dispatched.",
            reset_token=reset_token if settings.is_development else None,
        )

    async def reset_password(self, request: ResetPasswordRequest) -> ResetPasswordResponse:
        """
        Validates the password reset token, updates the user's password hash with bcrypt,
        resets failed login attempts, and unlocks the account if previously locked.
        """
        try:
            payload = decode_token(request.token)
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset token has expired. Please request a new one.",
            )
        except (jwt.PyJWTError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or malformed password reset token.",
            )

        if payload.get("type") != TokenTypes.PASSWORD_RESET.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type for password reset.",
            )

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Malformed token subject identifier.",
            )

        try:
            user_uuid = uuid.UUID(user_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Malformed token subject UUID.",
            )

        user = await self.user_service.get_by_id(user_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account associated with this token was not found.",
            )

        # Secure new password with bcrypt
        user.password_hash = get_password_hash(request.new_password)
        user.failed_login_attempts = 0
        user.is_locked = False
        await self.db.commit()
        await self.db.refresh(user)

        return ResetPasswordResponse(
            message="Password has been reset successfully. You may now log in with your new password.",
        )
