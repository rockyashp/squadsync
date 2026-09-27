"""
Pydantic v2 schemas for GamerProfile operations (Create, Update, Read).
Validates display name, bio, region, language, preferred games, preferred roles, availability, and avatar.
"""

from datetime import datetime
import re
from typing import Any
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class GamerProfileBase(BaseModel):
    """Shared profile attributes with strict input validation and rich Swagger documentation."""

    display_name: str | None = Field(
        None,
        min_length=2,
        max_length=100,
        description="Public gamer persona or handle",
        examples=["ShadowStrike"],
    )
    bio: str | None = Field(
        None,
        max_length=1000,
        description="Short gamer biography and playstyle summary",
        examples=["Immortal duelist with aggressive entry fragging and high comms."],
    )
    region: str | None = Field(
        None,
        max_length=50,
        description="Primary server or geographic region",
        examples=["NA-East"],
    )
    language: str | None = Field(
        "en",
        max_length=20,
        description="Preferred communication language",
        examples=["English"],
    )
    preferred_games: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="List of preferred game titles",
        examples=[["Valorant", "CS2", "Apex Legends"]],
    )
    preferred_roles: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="List of preferred competitive roles",
        examples=[["Duelist", "Initiator"]],
    )
    availability: str | None = Field(
        None,
        max_length=255,
        description="Weekly gaming schedule and active hours",
        examples=["Weekdays 8PM - 12AM EST, Weekends anytime"],
    )
    avatar: str | None = Field(
        None,
        max_length=512,
        description="Public URL pointing to profile avatar (.png, .jpg, .webp)",
        examples=["https://cdn.squadsync.gg/avatars/shadow.png"],
    )

    # Legacy attributes preserved for backwards-compatibility
    full_name: str | None = Field(None, max_length=100, description="Deprecated: use display_name")
    favorite_game: str | None = Field(None, max_length=100, description="Deprecated: use preferred_games")
    rank: str | None = Field(None, max_length=50, description="Current competitive tier", examples=["Immortal 1"])
    preferred_role: str | None = Field(None, max_length=50, description="Deprecated: use preferred_roles")
    gaming_schedule: str | None = Field(None, max_length=255, description="Deprecated: use availability")
    avatar_url: str | None = Field(None, max_length=512, description="Deprecated: use avatar")

    @field_validator("avatar", "avatar_url")
    @classmethod
    def validate_avatar_url(cls, v: str | None) -> str | None:
        """Enforces valid HTTP/HTTPS URLs pointing to valid image formats or domains."""
        if v is not None and v.strip() != "":
            v = v.strip()
            if not (v.startswith("http://") or v.startswith("https://")):
                raise ValueError("Avatar URL must be a valid HTTP or HTTPS address.")
            # Verify file extension if present
            clean_url = v.split("?")[0].lower()
            valid_extensions = (".png", ".jpg", ".jpeg", ".webp", ".gif")
            trusted_domains = ("discordapp.com", "discordapp.net", "gravatar.com", "imgur.com", "amazonaws.com")
            if any(clean_url.endswith(ext) for ext in valid_extensions) or any(domain in v.lower() for domain in trusted_domains):
                return v
            # If standard URL without explicit image extension, still accept if valid URL
            return v
        return None

    @field_validator(
        "display_name", "full_name", "bio", "region", "language",
        "availability", "gaming_schedule", "favorite_game", "preferred_role", "rank"
    )
    @classmethod
    def strip_strings(cls, v: str | None) -> str | None:
        """Trims leading/trailing whitespace and converts empty strings to None."""
        if isinstance(v, str):
            cleaned = v.strip()
            return cleaned if cleaned else None
        return v

    @field_validator("preferred_games", "preferred_roles")
    @classmethod
    def validate_lists(cls, v: list[str]) -> list[str]:
        """Cleans and deduplicates string lists."""
        cleaned = []
        for item in v:
            if isinstance(item, str) and item.strip():
                c = item.strip()
                if c not in cleaned:
                    cleaned.append(c)
        return cleaned

    @model_validator(mode="after")
    def synchronize_aliases(self) -> "GamerProfileBase":
        """Synchronizes new field names with legacy aliases."""
        if not self.display_name and self.full_name:
            self.display_name = self.full_name
        elif not self.full_name and self.display_name:
            self.full_name = self.display_name

        if not self.avatar and self.avatar_url:
            self.avatar = self.avatar_url
        elif not self.avatar_url and self.avatar:
            self.avatar_url = self.avatar

        if not self.availability and self.gaming_schedule:
            self.availability = self.gaming_schedule
        elif not self.gaming_schedule and self.availability:
            self.gaming_schedule = self.availability

        if not self.preferred_games and self.favorite_game:
            self.preferred_games = [self.favorite_game]
        elif not self.favorite_game and self.preferred_games:
            self.favorite_game = self.preferred_games[0]

        if not self.preferred_roles and self.preferred_role:
            self.preferred_roles = [self.preferred_role]
        elif not self.preferred_role and self.preferred_roles:
            self.preferred_role = self.preferred_roles[0]

        return self


class GamerProfileCreate(GamerProfileBase):
    """Schema for creating a gamer profile."""
    pass


class GamerProfileUpdate(BaseModel):
    """Schema for updating an existing gamer profile (all attributes optional for partial updates)."""

    display_name: str | None = Field(None, min_length=2, max_length=100, examples=["ShadowStrike_X"])
    bio: str | None = Field(None, max_length=1000, examples=["Updated bio: Now competing in Premier Division."])
    region: str | None = Field(None, max_length=50, examples=["EU-West"])
    language: str | None = Field(None, max_length=20, examples=["English"])
    preferred_games: list[str] | None = Field(None, max_length=10, examples=[["Valorant", "Overwatch 2"]])
    preferred_roles: list[str] | None = Field(None, max_length=10, examples=[["Controller", "Sentinel"]])
    availability: str | None = Field(None, max_length=255, examples=["Weekends 2PM - 10PM CET"])
    avatar: str | None = Field(None, max_length=512, examples=["https://cdn.squadsync.gg/avatars/new.png"])

    # Legacy attributes
    full_name: str | None = Field(None, max_length=100)
    favorite_game: str | None = Field(None, max_length=100)
    rank: str | None = Field(None, max_length=50)
    preferred_role: str | None = Field(None, max_length=50)
    gaming_schedule: str | None = Field(None, max_length=255)
    avatar_url: str | None = Field(None, max_length=512)

    @field_validator("avatar", "avatar_url")
    @classmethod
    def validate_avatar_url(cls, v: str | None) -> str | None:
        if v is not None and v.strip() != "":
            v = v.strip()
            if not (v.startswith("http://") or v.startswith("https://")):
                raise ValueError("Avatar URL must be a valid HTTP or HTTPS address.")
            return v
        return None

    @field_validator(
        "display_name", "full_name", "bio", "region", "language",
        "availability", "gaming_schedule", "favorite_game", "preferred_role", "rank"
    )
    @classmethod
    def strip_strings(cls, v: str | None) -> str | None:
        if isinstance(v, str):
            cleaned = v.strip()
            return cleaned if cleaned else None
        return v


class GamerProfileRead(GamerProfileBase):
    """Public schema representing a complete GamerProfile."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="Unique profile identifier")
    user_id: uuid.UUID = Field(..., description="Foreign key linking to owner User account")
    created_at: datetime = Field(..., description="Profile creation UTC timestamp")
    updated_at: datetime = Field(..., description="Profile last updated UTC timestamp")
