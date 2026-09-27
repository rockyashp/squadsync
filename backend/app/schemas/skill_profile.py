"""
Pydantic v2 schemas for Skill Profile Generator requests and responses.
Provides structured validation for the 6 skill dimensions and explainability metadata.
"""

from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.role_classifier import GamerDNAInput, OfficialGameStatsInput


class SkillDimensionDetail(BaseModel):
    """Evaluation detail for an individual skill dimension."""
    name: str = Field(description="Name of the skill dimension")
    score: float = Field(ge=0.0, le=100.0, description="Normalized score (0-100)")
    tier: str = Field(description="Qualitative competitive tier (e.g. S-Tier, A-Tier)")
    explanation: str = Field(description="Human-readable justification for the score")
    signal_breakdown: dict[str, float] = Field(
        default_factory=dict, description="Relative contribution of DNA vs. telemetry"
    )

    model_config = ConfigDict(from_attributes=True)


class SkillProfileResponse(BaseModel):
    """Full 6-dimensional competitive skill profile response."""
    overall_score: float = Field(description="Composite competitive rating (0-100)")
    overall_tier: str = Field(description="Overall qualitative tier classification")
    mechanical_skill: SkillDimensionDetail = Field(description="Mechanical execution and aim score")
    communication: SkillDimensionDetail = Field(description="Callouts and utility sync score")
    leadership: SkillDimensionDetail = Field(description="Shotcalling and round command score")
    consistency: SkillDimensionDetail = Field(description="Match-to-match stability score")
    decision_making: SkillDimensionDetail = Field(description="Situational risk-reward score")
    game_sense: SkillDimensionDetail = Field(description="Macro map reading and rotation score")
    radar_chart: dict[str, float] = Field(description="Normalized coordinates for radar chart visualization")
    top_strengths: list[str] = Field(description="Top 2 standout competitive capabilities")
    growth_areas: list[str] = Field(description="Recommended areas for targeted improvement")

    model_config = ConfigDict(from_attributes=True)


class SkillProfileEvaluateRequest(BaseModel):
    """Payload for evaluating skill profile on arbitrary inputs."""
    gamer_dna: GamerDNAInput = Field(default_factory=GamerDNAInput, description="Gamer DNA psychometrics")
    official_stats: OfficialGameStatsInput = Field(
        default_factory=OfficialGameStatsInput, description="Official game statistics"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "gamer_dna": {
                    "leadership": 85.0,
                    "communication": 80.0,
                    "strategy": 75.0,
                    "aggression": 90.0,
                    "teamwork": 65.0,
                    "confidence": 88.0,
                },
                "official_stats": {
                    "win_rate": 58.0,
                    "kd_ratio": 1.45,
                    "kda": 2.2,
                    "matches_played": 120,
                    "headshot_pct": 31.0,
                },
            }
        }
    )
