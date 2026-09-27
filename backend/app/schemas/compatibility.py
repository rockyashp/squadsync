"""
Pydantic v2 validation schemas for the AI Compatibility Engine.
Defines schemas for pairwise player comparison inputs and detailed compatibility reports.
"""

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class PlayerProfileComparisonSchema(BaseModel):
    """Profile features for an individual player in a compatibility comparison."""
    username: str = Field(default="Player", description="Gamer display moniker")

    # Psychometrics (Gamer DNA)
    leadership: float = Field(default=50.0, ge=0.0, le=100.0, description="Leadership trait score")
    communication: float = Field(default=50.0, ge=0.0, le=100.0, description="Communication trait score")
    aggression: float = Field(default=50.0, ge=0.0, le=100.0, description="Aggression trait score")
    strategy: float = Field(default=50.0, ge=0.0, le=100.0, description="Strategy trait score")

    # Logistics
    region: str = Field(default="NA-East", description="Server region e.g. NA-East, EU-West")
    languages: list[str] = Field(default_factory=lambda: ["en"], description="Fluent languages")
    schedule_slots: list[str] = Field(default_factory=list, description="Active gaming time windows")

    # Competitive Telemetry
    rank_rating: int = Field(default=1000, description="Normalized skill MMR/Elo")
    rank_tier: str | None = Field(default=None, description="Competitive tier e.g. Diamond 2")
    win_rate: float = Field(default=50.0, ge=0.0, le=100.0, description="Competitive win percentage")
    preferred_roles: list[str] = Field(
        default_factory=list, description="Preferred tactical roles e.g. ['Duelist', 'Leader']"
    )

    model_config = ConfigDict(extra="ignore")


class CompatibilityCompareRequest(BaseModel):
    """Request payload comparing Player A and Player B."""
    player_a: PlayerProfileComparisonSchema = Field(description="Features for Player A")
    player_b: PlayerProfileComparisonSchema = Field(description="Features for Player B")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "player_a": {
                    "username": "ViperMain",
                    "leadership": 85.0,
                    "communication": 80.0,
                    "aggression": 60.0,
                    "strategy": 88.0,
                    "region": "NA-East",
                    "languages": ["en"],
                    "schedule_slots": ["weekday_evening", "weekend_afternoon"],
                    "rank_rating": 1450,
                    "win_rate": 56.5,
                    "preferred_roles": ["Leader", "Controller"],
                },
                "player_b": {
                    "username": "JettCarry",
                    "leadership": 50.0,
                    "communication": 75.0,
                    "aggression": 92.0,
                    "strategy": 65.0,
                    "region": "NA-East",
                    "languages": ["en"],
                    "schedule_slots": ["weekday_evening", "weekend_evening"],
                    "rank_rating": 1500,
                    "win_rate": 57.0,
                    "preferred_roles": ["Duelist"],
                },
            }
        }
    )


class CompatibilityReportResponse(BaseModel):
    """Complete multi-dimensional AI compatibility comparison report."""
    player_a_name: str = Field(description="Moniker of Player A")
    player_b_name: str = Field(description="Moniker of Player B")
    compatibility_score: float = Field(description="Weighted overall compatibility percentage (0-100)")
    tier: str = Field(description="Qualitative duo tier classification")
    dimension_scores: dict[str, float] = Field(description="Scores across all 10 individual dimensions")
    strengths: list[str] = Field(description="Standout synergy advantages")
    weaknesses: list[str] = Field(description="Areas of sub-optimal alignment")
    recommendations: list[str] = Field(description="Actionable duo tactical recommendations")
    risk_factors: list[str] = Field(description="Critical clash warnings and co-op blockers")

    model_config = ConfigDict(from_attributes=True)
