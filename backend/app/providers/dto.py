"""
Data Transfer Objects (DTOs) for Game Integration Framework.
Standardizes data exchange between external game adapters and internal domain services.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class AccountVerificationResult:
    """
    Standardized payload returned when verifying an external game account.
    """
    is_valid: bool
    account_identifier: str
    in_game_name: str
    tagline: str | None = None
    region: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None


@dataclass(frozen=True)
class ProviderProfileData:
    """
    Standardized third-party gamer profile details.
    """
    account_identifier: str
    in_game_name: str
    tagline: str | None = None
    region: str | None = None
    avatar_url: str | None = None
    account_level: int | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderStatsData:
    """
    Standardized competitive statistics and telemetry for a given season or mode.
    """
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
    raw_stats: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderSyncResult:
    """
    Comprehensive result of synchronizing an external game account.
    """
    is_success: bool
    profile: ProviderProfileData | None = None
    stats: list[ProviderStatsData] = field(default_factory=list)
    synced_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error_message: str | None = None
