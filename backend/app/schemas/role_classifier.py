"""
Pydantic v2 schemas for the Gamer Role Classification Engine.
Defines strict validation for the 4 classification inputs and rich explainable outputs.
"""

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class GamerDNAInput(BaseModel):
    """Gamer DNA psychometric feature vector (0.0 to 100.0)."""
    leadership: float = Field(default=50.0, ge=0.0, le=100.0, description="Leadership trait score")
    communication: float = Field(default=50.0, ge=0.0, le=100.0, description="Communication trait score")
    strategy: float = Field(default=50.0, ge=0.0, le=100.0, description="Strategy trait score")
    aggression: float = Field(default=50.0, ge=0.0, le=100.0, description="Aggression trait score")
    teamwork: float = Field(default=50.0, ge=0.0, le=100.0, description="Teamwork trait score")
    confidence: float = Field(default=50.0, ge=0.0, le=100.0, description="Confidence trait score")

    model_config = ConfigDict(extra="ignore")


class OfficialGameStatsInput(BaseModel):
    """Official competitive telemetry and publisher stats."""
    win_rate: float = Field(default=50.0, ge=0.0, le=100.0, description="Win percentage (0-100)")
    kd_ratio: float = Field(default=1.0, ge=0.0, description="Kill to Death ratio")
    kda: float = Field(default=2.0, ge=0.0, description="(Kills + Assists) / Deaths")
    matches_played: int = Field(default=50, ge=0, description="Total competitive matches recorded")
    headshot_pct: float | None = Field(default=None, ge=0.0, le=100.0, description="Headshot percentage")
    score_per_round: float | None = Field(default=None, ge=0.0, description="Average damage or combat score per round")
    rank: str | None = Field(default=None, description="Competitive tier e.g. Diamond 3")
    rank_rating: int | None = Field(default=None, description="Rank rating or MMR points")
    favorite_heroes_or_agents: list[str] = Field(
        default_factory=list, description="Top played agents/heroes e.g. ['Jett', 'Reyna']"
    )

    model_config = ConfigDict(extra="ignore")


class RoleClassifierEvaluateRequest(BaseModel):
    """
    Consolidated payload containing the 4 classification inputs:
    1. Gamer DNA feature vector
    2. Official game statistics
    3. Preferred roles
    4. Preferred games
    """
    gamer_dna: GamerDNAInput = Field(default_factory=GamerDNAInput, description="Psychometric trait scores")
    official_stats: OfficialGameStatsInput = Field(
        default_factory=OfficialGameStatsInput, description="Official competitive telemetry"
    )
    preferred_roles: list[str] = Field(
        default_factory=list,
        description="Declared preferred tactical roles e.g. ['Duelist', 'Leader']",
        examples=[["Duelist", "Leader"]],
    )
    preferred_games: list[str] = Field(
        default_factory=list,
        description="Games currently played e.g. ['Valorant', 'Dota 2']",
        examples=[["Valorant", "Dota 2"]],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "gamer_dna": {
                    "leadership": 82.0,
                    "communication": 78.0,
                    "strategy": 65.0,
                    "aggression": 88.0,
                    "teamwork": 60.0,
                    "confidence": 85.0,
                },
                "official_stats": {
                    "win_rate": 56.5,
                    "kd_ratio": 1.38,
                    "kda": 2.15,
                    "matches_played": 142,
                    "headshot_pct": 28.5,
                    "favorite_heroes_or_agents": ["Jett", "Reyna"],
                },
                "preferred_roles": ["Duelist"],
                "preferred_games": ["Valorant"],
            }
        }
    )


class SignalContribution(BaseModel):
    """Breakdown of individual signals contributing to a role."""
    dna: float
    stats: float
    preference: float
    game: float


class RoleClassificationResponse(BaseModel):
    """
    Primary output schema for Role Classification.
    Provides Primary Role, Secondary Role, Confidence Score, and Explainable AI Reasoning.
    """
    primary_role: str = Field(description="Dominant classified archetype e.g. Duelist, Leader, Support")
    secondary_role: str = Field(description="Secondary complementary archetype")
    confidence_score: float = Field(description="Mathematically normalized model confidence (0.0 to 1.0)")
    reasoning: str = Field(description="Explainable AI breakdown detailing evidence from all 4 inputs")
    personality: str = Field(description="Stylized gamer persona moniker e.g. 'The Fearless Vanguard'")
    role_affinities: dict[str, float] = Field(description="Computed affinity percentage across all 6 roles")
    signal_contributions: dict[str, dict[str, float]] = Field(
        default_factory=dict, description="Signal breakdown per role"
    )
    feature_importance: dict[str, float] = Field(
        default_factory=dict, description="Normalized influence of each input group on primary role"
    )

    model_config = ConfigDict(from_attributes=True)


class RoleClassifierConfigResponse(BaseModel):
    """Configuration metadata response."""
    supported_roles: list[str]
    signal_weights: dict[str, float]
    stat_benchmarks: dict[str, Any]
    role_descriptions: dict[str, str]
