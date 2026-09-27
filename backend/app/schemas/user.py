"""
Pydantic v2 schemas for User entity representations.
"""

from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base shared attributes for User."""
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Unique alphanumeric username (underscores and hyphens allowed)",
        examples=["shadow_striker"],
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address",
        examples=["player1@squadsync.gg"],
    )


class UserRead(UserBase):
    """Public representation of User profile."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="Unique user identifier")
    is_active: bool = Field(..., description="Whether user account is active")
    is_locked: bool = Field(..., description="Whether user account is locked due to failed logins")
    is_admin: bool = Field(default=False, description="Whether user has administrator privileges (BR-4)")
    created_at: datetime = Field(..., description="Account creation UTC timestamp")
    updated_at: datetime = Field(..., description="Account last updated UTC timestamp")
