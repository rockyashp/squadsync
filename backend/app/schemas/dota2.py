"""
Steam Authentication & Dota 2 OpenDota Pydantic v2 schemas.
Standardized models for Steam OpenID login URLs, OpenID callbacks, hero analytics,
recent match telemetry, and synchronized Dota 2 profiles.
"""

from datetime import datetime, timezone
from typing import Any
import uuid

from pydantic import BaseModel, ConfigDict, Field


class SteamLoginUrlResponse(BaseModel):
    """
    Response model providing the Steam OpenID 2.0 authentication URL.
    """
    login_url: str = Field(
        ...,
        description="Full Steam OpenID 2.0 redirect URL for initiating user authentication",
    )
    realm: str = Field(
        ...,
        description="Application realm passed to Steam OpenID provider",
    )
    return_to: str = Field(
        ...,
        description="Callback URL where Steam will redirect after authentication",
    )


class Dota2HeroStat(BaseModel):
    """
    Performance telemetry for a specific Dota 2 hero.
    """
    hero_id: int = Field(..., description="Unique Dota 2 hero ID (e.g. 1 for Anti-Mage, 74 for Invoker)")
    hero_name: str = Field(..., description="Display name of the hero")
    games: int = Field(..., description="Total matches played with this hero")
    wins: int = Field(..., description="Total wins achieved with this hero")
    win_rate: float = Field(..., description="Win percentage (0.0 to 100.0)")


class Dota2RecentMatch(BaseModel):
    """
    Telemetry for an individual recent competitive or public match.
    """
    match_id: int = Field(..., description="Valve match ID")
    hero_id: int = Field(..., description="Hero played in this match")
    hero_name: str = Field(..., description="Display name of the hero played")
    kills: int = Field(default=0)
    deaths: int = Field(default=0)
    assists: int = Field(default=0)
    kda: float = Field(..., description="Calculated KDA ratio (Kills + Assists) / Deaths")
    won: bool = Field(..., description="Whether the player's team won the match")
    duration_minutes: float = Field(..., description="Match duration in minutes")
    start_time: int | None = Field(default=None, description="Unix timestamp of match start")


class Dota2TelemetrySummary(BaseModel):
    """
    Aggregated and normalized Dota 2 competitive profile data.
    """
    steam_id: str = Field(..., description="64-bit Steam ID")
    dota_account_id: int = Field(..., description="32-bit Dota 2 Account ID")
    player_name: str = Field(..., description="Steam persona name / gamer handle")
    avatar_url: str | None = Field(default=None, description="Direct URL to full-resolution avatar")
    mmr: int | None = Field(default=None, description="Estimated or competitive MMR rating")
    rank: str = Field(..., description="Human-readable medal rank (e.g., 'Divine 3', 'Immortal #120')")
    rank_tier: int | None = Field(default=None, description="OpenDota 2-digit rank tier code")
    leaderboard_rank: int | None = Field(default=None, description="Immortal leaderboard placement")
    wins: int = Field(..., description="Total competitive and unranked wins")
    losses: int = Field(..., description="Total losses")
    win_rate: float = Field(..., description="Overall win percentage")
    favorite_heroes: list[Dota2HeroStat] = Field(default_factory=list, description="Top 5 most played heroes")
    recent_matches: list[Dota2RecentMatch] = Field(default_factory=list, description="Recent 10 match summaries")


class Dota2SyncResponse(BaseModel):
    """
    Complete synchronization response for a linked Steam & Dota 2 account.
    """
    model_config = ConfigDict(from_attributes=True)

    account_id: uuid.UUID = Field(..., description="Internal GameAccount UUID in SquadSync")
    user_id: uuid.UUID = Field(..., description="SquadSync User UUID")
    steam_id: str = Field(..., description="64-bit Steam ID")
    player_name: str = Field(..., description="Steam persona name / in-game handle")
    avatar: str | None = Field(default=None, description="Avatar image URL")
    mmr: int | None = Field(default=None, description="MMR rating")
    rank: str = Field(..., description="Medal rank")
    wins: int = Field(default=0)
    losses: int = Field(default=0)
    favorite_heroes: list[Dota2HeroStat] = Field(default_factory=list)
    recent_matches: list[Dota2RecentMatch] = Field(default_factory=list)
    is_verified: bool = Field(..., description="Whether account ownership was verified via OpenID")
    last_synced_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of last telemetry synchronization",
    )
    sync_mode: str = Field(default="realtime", description="'realtime' or 'background'")
    raw_profile_data: dict[str, Any] | None = Field(
        default=None,
        description="Raw publisher telemetry JSON payload stored in PostgreSQL JSONB",
    )
