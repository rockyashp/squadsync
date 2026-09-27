"""
Data transfer objects and internal models for the AI Compatibility Engine.
"""

from dataclasses import dataclass, field
from typing import Any
import uuid


@dataclass
class PlayerComparisonInput:
    """Consolidated profile representation for compatibility comparison."""
    user_id: uuid.UUID | None = None
    username: str = "Player"

    # Psychometrics (Gamer DNA) (0.0 to 100.0)
    leadership: float = 50.0
    communication: float = 50.0
    aggression: float = 50.0
    strategy: float = 50.0

    # Logistics
    region: str = "NA-East"
    languages: list[str] = field(default_factory=lambda: ["en"])
    schedule_slots: list[str] = field(default_factory=list)

    # Competitive Telemetry
    rank_rating: int = 1000  # Normalized skill MMR/Elo scale
    rank_tier: str | None = None
    win_rate: float = 50.0
    preferred_roles: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DimensionScore:
    """Individual dimension evaluation result."""
    dimension: str
    score: float
    weight: float
    assessment: str


@dataclass(frozen=True)
class CompatibilityReport:
    """Consolidated compatibility report output."""
    player_a_name: str
    player_b_name: str
    compatibility_score: float
    tier: str
    dimension_scores: dict[str, float]
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    risk_factors: list[str]
