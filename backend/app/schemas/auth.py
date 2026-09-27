"""
Pydantic v2 schemas for Authentication workflows (Register, Login, Token, Refresh).
"""

import re
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegisterRequest(BaseModel):
    """Payload for registering a new user account."""
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Alphanumeric username with hyphens and underscores",
        examples=["pro_gamer99"],
    )
    email: EmailStr = Field(
        ...,
        description="User email address",
        examples=["pro_gamer@squadsync.gg"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Strong password containing uppercase, lowercase, digit, and special symbol",
        examples=["P@ssw0rd123!"],
    )

    @field_validator("password")
    @classmethod
    def validate_strong_password(cls, v: str) -> str:
        """Enforces enterprise password strength policy."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter (A-Z).")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter (a-z).")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit (0-9).")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", v):
            raise ValueError("Password must contain at least one special character.")
        return v


class UserLoginRequest(BaseModel):
    """Payload for authenticating with username or email and password."""
    username_or_email: str = Field(
        ...,
        min_length=3,
        description="Username or registered email address",
        examples=["pro_gamer99"],
    )
    password: str = Field(
        ...,
        min_length=1,
        description="User account password",
        examples=["P@ssw0rd123!"],
    )


class TokenResponse(BaseModel):
    """JWT bearer token pair issued upon successful authentication."""
    access_token: str = Field(..., description="Short-lived JWT access token")
    refresh_token: str = Field(..., description="Longer-lived JWT refresh token")
    token_type: str = Field(default="bearer", description="Token authentication scheme")
    expires_in: int = Field(..., description="Access token expiration window in seconds")


class TokenRefreshRequest(BaseModel):
    """Payload to renew an expired access token using a refresh token."""
    refresh_token: str = Field(..., description="Valid JWT refresh token")


class LogoutResponse(BaseModel):
    """Standard response returned upon logout."""
    message: str = Field(default="Logged out successfully", description="Logout confirmation message")


class ForgotPasswordRequest(BaseModel):
    """Payload to initiate a password reset sequence."""
    email: EmailStr = Field(
        ...,
        description="Registered user email address to receive password reset link",
        examples=["pro_gamer@squadsync.gg"],
    )


class ForgotPasswordResponse(BaseModel):
    """Response confirming that password reset request was accepted."""
    message: str = Field(
        default="If the email is registered, a password reset link has been dispatched.",
        description="User notification message",
    )
    reset_token: str | None = Field(
        default=None,
        description="Password reset token (exposed in development/test environment for verification)",
    )


class ResetPasswordRequest(BaseModel):
    """Payload to complete password reset using a cryptographically signed reset token."""
    token: str = Field(..., description="Valid, unexpired password reset token")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New strong password",
        examples=["N3wStrongP@ssw0rd!"],
    )

    @field_validator("new_password")
    @classmethod
    def validate_strong_password(cls, v: str) -> str:
        """Enforces enterprise password strength policy."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter (A-Z).")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter (a-z).")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit (0-9).")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", v):
            raise ValueError("Password must contain at least one special character.")
        return v


class ResetPasswordResponse(BaseModel):
    """Confirmation returned upon successful password reset."""
    message: str = Field(
        default="Password has been reset successfully. You may now log in with your new password.",
        description="Success confirmation message",
    )
