"""
Riot Games and Riot Sign-On (RSO) Pydantic v2 schemas.
Standardized schemas for RSO authorization URLs, callbacks, player telemetry,
and synchronized Riot/Valorant profiles:
- PUUID
- Summoner Name
- Rank
- Current Season
- Preferred Agent
- Competitive Tier
"""

from datetime import datetime, timezone
from typing import Any
import uuid

from pydantic import BaseModel, ConfigDict, Field


class RiotLoginUrlResponse(BaseModel):
    """
    Response schema returning the Riot Sign-On (RSO) OAuth2 authorization URL.
    """
    auth_url: str = Field(
        ...,
        description="Riot Sign-On OAuth2 authorization redirect URL",
    )
    client_id_configured: bool = Field(
        ...,
        description="Whether a valid Riot Client ID is configured in settings",
    )
    redirect_uri: str = Field(
        ...,
        description="Redirect URI registered with Riot Games Developer Portal",
    )
    state: str | None = Field(
        default=None,
        description="OAuth2 state token for CSRF protection",
    )


class RiotCallbackRequest(BaseModel):
    """
    Payload sent during RSO OAuth2 callback token exchange.
    """
    code: str = Field(..., description="RSO authorization code returned in callback redirect")
    state: str | None = Field(default=None, description="Optional OAuth2 state parameter")


class RiotTelemetrySummary(BaseModel):
    """
    Normalized competitive telemetry representation for Riot Games (Valorant).
    """
    puuid: str = Field(..., description="Unique immutable Riot Player Universal Unique Identifier")
    summoner_name: str = Field(..., description="Player in-game handle (Riot ID gameName#tagLine)")
    rank: str = Field(..., description="Display rank title (e.g., 'Immortal 2', 'Radiant')")
    current_season: str = Field(..., description="Current competitive act/season (e.g., 'Episode 8: Act 3')")
    preferred_agent: str = Field(..., description="Most played competitive agent or champion (e.g., 'Jett', 'Reyna')")
    competitive_tier: int = Field(..., description="Numerical tier rating (e.g., 25 for Immortal 2)")
    wins: int = Field(default=0, description="Total wins in current season")
    losses: int = Field(default=0, description="Total losses in current season")
    win_rate: float = Field(default=0.0, description="Win percentage in current season")


class RiotSyncResponse(BaseModel):
    """
    Comprehensive synchronization response for a linked Riot Games account.
    """
    model_config = ConfigDict(from_attributes=True)

    account_id: uuid.UUID = Field(..., description="Internal GameAccount UUID")
    user_id: uuid.UUID = Field(..., description="User UUID")
    puuid: str = Field(..., description="Riot PUUID")
    summoner_name: str = Field(..., description="Summoner name / Riot handle")
    rank: str = Field(..., description="Rank title")
    current_season: str = Field(..., description="Competitive season/act")
    preferred_agent: str = Field(..., description="Preferred agent")
    competitive_tier: int = Field(..., description="Competitive tier integer")
    wins: int = Field(default=0)
    losses: int = Field(default=0)
    win_rate: float = Field(default=0.0)
    is_verified: bool = Field(..., description="Account ownership verification status")
    last_synced_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of last telemetry synchronization",
    )
    raw_profile_data: dict[str, Any] | None = Field(
        default=None,
        description="Raw publisher telemetry JSON payload stored in PostgreSQL JSONB",
    )
