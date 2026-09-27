"""
Pydantic v2 validation schemas for AI Explanation Engine.
Defines schemas for explanation requests, player contexts, and structured explanation outputs.
"""

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class PlayerExplanationInputSchema(BaseModel):
    """Contextual features of a player used for explanation generation."""
    username: str = Field(default="Player", description="Gamer display moniker")

    # Psychometrics (Gamer DNA)
    leadership: float = Field(default=50.0, ge=0.0, le=100.0, description="Leadership trait score")
    communication: float = Field(default=50.0, ge=0.0, le=100.0, description="Communication trait score")
    aggression: float = Field(default=50.0, ge=0.0, le=100.0, description="Aggression trait score")
    strategy: float = Field(default=50.0, ge=0.0, le=100.0, description="Strategy trait score")
    teamwork: float = Field(default=50.0, ge=0.0, le=100.0, description="Teamwork trait score")

    # Roles
    primary_role: str = Field(default="Support", description="Primary tactical role e.g. Duelist, Controller")
    secondary_role: str | None = Field(default=None, description="Secondary flex role")
    preferred_roles: list[str] = Field(default_factory=list, description="All preferred roles")

    # Competitive Telemetry
    rank: str = Field(default="Gold 1", description="Competitive tier e.g. Diamond 2")
    rank_rating: int = Field(default=1000, description="Normalized skill MMR/Elo")
    win_rate: float = Field(default=50.0, ge=0.0, le=100.0, description="Competitive win percentage")
    matches_played: int = Field(default=20, ge=0, description="Matches played in current season")
    kd_ratio: float = Field(default=1.0, ge=0.0, description="Kill/Death ratio")

    # Logistics
    region: str = Field(default="NA-East", description="Server region e.g. NA-East")
    languages: list[str] = Field(default_factory=lambda: ["en"], description="Fluent languages")
    schedule_slots: list[str] = Field(default_factory=list, description="Active gaming windows")

    model_config = ConfigDict(extra="ignore")


class ExplanationCompareRequest(BaseModel):
    """Request payload to generate human-readable compatibility explanation between two players."""
    player_a: PlayerExplanationInputSchema = Field(description="Contextual profile for Player A")
    player_b: PlayerExplanationInputSchema = Field(description="Contextual profile for Player B")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "player_a": {
                    "username": "ViperMain",
                    "leadership": 85.0,
                    "communication": 82.0,
                    "aggression": 58.0,
                    "strategy": 90.0,
                    "primary_role": "Controller",
                    "secondary_role": "Leader",
                    "preferred_roles": ["Controller", "Leader"],
                    "rank": "Diamond 3",
                    "rank_rating": 1450,
                    "win_rate": 56.0,
                    "matches_played": 85,
                    "region": "NA-East",
                    "languages": ["en"],
                    "schedule_slots": ["weekday_evening"],
                },
                "player_b": {
                    "username": "JettCarry",
                    "leadership": 45.0,
                    "communication": 78.0,
                    "aggression": 92.0,
                    "strategy": 65.0,
                    "primary_role": "Duelist",
                    "secondary_role": "Initiator",
                    "preferred_roles": ["Duelist"],
                    "rank": "Diamond 2",
                    "rank_rating": 1400,
                    "win_rate": 57.5,
                    "matches_played": 90,
                    "region": "NA-East",
                    "languages": ["en"],
                    "schedule_slots": ["weekday_evening"],
                },
            }
        }
    )


class ExplanationResponse(BaseModel):
    """Comprehensive human-readable explanation output."""
    headline: str = Field(description="Executive summary headline characterizing the duo dynamic")
    player_a_name: str = Field(description="Moniker of Player A")
    player_b_name: str = Field(description="Moniker of Player B")
    compatibility_score: float = Field(description="Weighted overall compatibility percentage (0-100)")
    tier: str = Field(description="Qualitative duo tier classification")
    why_they_match: list[str] = Field(description="Detailed narrative explaining why two players match")
    why_they_dont_match: list[str] = Field(description="Detailed narrative explaining friction points or why they don't match")
    strengths: list[str] = Field(description="Deep breakdown of duo strengths")
    weaknesses: list[str] = Field(description="Deep breakdown of duo vulnerabilities")
    improvement_suggestions: list[str] = Field(description="Actionable tactical and communication coaching advice")
    confidence_score: float = Field(description="Algorithmic confidence in the explanation (0.0 to 1.0)")

    model_config = ConfigDict(from_attributes=True)
