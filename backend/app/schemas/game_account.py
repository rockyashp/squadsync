"""
GameAccount and PlayerStat Pydantic v2 schemas.
Validation and serialization models for external game linking, telemetry, and synchronization.
"""

from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GameAccountLinkRequest(BaseModel):
    """
    Request schema for linking an external gaming account.
    """
    platform: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Gaming platform or publisher (e.g., 'riot', 'steam', 'epic', 'battlenet')",
        examples=["riot"],
    )
    game_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Game title (e.g., 'Valorant', 'League of Legends', 'CS2')",
        examples=["Valorant"],
    )
    account_identifier: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Immutable publisher ID (e.g., Riot PUUID, SteamID64)",
        examples=["riot_puuid_abc123456789"],
    )
    in_game_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Gamer handle or summoner name",
        examples=["ValkyriePrime"],
    )
    tagline: str | None = Field(
        None,
        max_length=50,
        description="Gamer tagline/discriminator (e.g., 'NA1', 'EUW')",
        examples=["NA1"],
    )
    region: str | None = Field(
        None,
        max_length=50,
        description="Game region (e.g., 'na', 'eu', 'ap')",
        examples=["na"],
    )
    is_primary: bool = Field(
        default=False,
        description="Whether this is the primary account for this game",
    )
    auth_payload: dict[str, Any] | None = Field(
        default=None,
        description="Optional provider verification credentials or OAuth tokens",
    )

    @field_validator("platform", "game_name", "account_identifier", "in_game_name", mode="before")
    @classmethod
    def strip_and_normalize(cls, v: str) -> str:
        if isinstance(v, str):
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Field cannot be empty or whitespace only")
            return cleaned
        return v

    @field_validator("tagline", "region", mode="before")
    @classmethod
    def strip_optional_fields(cls, v: str | None) -> str | None:
        if isinstance(v, str):
            cleaned = v.strip()
            return cleaned or None
        return v


class GameAccountUpdateRequest(BaseModel):
    """
    Request schema for updating an existing linked account.
    """
    in_game_name: str | None = Field(None, min_length=1, max_length=100)
    tagline: str | None = Field(None, max_length=50)
    region: str | None = Field(None, max_length=50)
    is_primary: bool | None = Field(None)

    @field_validator("in_game_name", "tagline", "region", mode="before")
    @classmethod
    def strip_text(cls, v: str | None) -> str | None:
        if isinstance(v, str):
            cleaned = v.strip()
            return cleaned or None
        return v


class PlayerStatRead(BaseModel):
    """
    Serialized competitive performance and telemetry stats.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    game_account_id: uuid.UUID
    user_id: uuid.UUID
    season: str
    game_mode: str
    rank: str | None = None
    rank_tier: int | None = None
    rank_rating: int | None = None
    peak_rank: str | None = None
    matches_played: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float | None = None
    kd_ratio: float | None = None
    headshot_percentage: float | None = None
    damage_per_round: float | None = None
    raw_stats_data: dict[str, Any] | None = None
    last_calculated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class GameAccountRead(BaseModel):
    """
    Serialized GameAccount details.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    game_name: str
    platform: str
    account_identifier: str
    in_game_name: str
    tagline: str | None = None
    full_handle: str | None = None
    region: str | None = None
    is_verified: bool
    is_primary: bool
    last_synced_at: datetime | None = None
    raw_profile_data: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class GameAccountSyncResponse(BaseModel):
    """
    Response schema returning the results of a provider synchronization operation.
    """
    account_id: uuid.UUID
    platform: str
    in_game_name: str
    tagline: str | None = None
    full_handle: str
    is_verified: bool
    synced_at: datetime
    stats_synced_count: int
    latest_rank: str | None = None
    latest_win_rate: float | None = None
    sync_message: str
