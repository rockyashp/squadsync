"""
Pydantic v2 validation schemas for Squad Recommendation Engine.
Defines schemas for Top 10 Teammates, Best 5-Player Squad, Missing Roles, and Confidence.
"""

from typing import Any
import uuid
from pydantic import BaseModel, ConfigDict, Field


class TeammateCandidateSchema(BaseModel):
    """Profile and compatibility breakdown for an individual ranked teammate."""
    user_id: str = Field(description="UUID of the candidate")
    username: str = Field(description="Display moniker")
    compatibility_score: float = Field(description="Pairwise compatibility percentage with the current user")
    primary_role: str = Field(description="Primary tactical archetype e.g. Duelist, Controller")
    secondary_role: str | None = Field(default=None, description="Secondary flex role")
    rank: str = Field(description="Competitive rank tier")
    mmr: int = Field(description="Skill rating / Elo")
    win_rate: float = Field(description="Win percentage")
    personality: str = Field(description="Persona moniker")
    synergy_highlights: list[str] = Field(default_factory=list, description="Specific co-op synergy reasons")

    model_config = ConfigDict(from_attributes=True)


class BestSquadMemberSchema(BaseModel):
    """Squad member details inside the best 5-player squad."""
    user_id: str = Field(description="UUID of the squadmate")
    username: str = Field(description="Display moniker")
    primary_role: str = Field(description="Assigned/Primary tactical archetype")
    secondary_role: str | None = Field(default=None, description="Secondary flex role")
    rank: str = Field(description="Competitive rank tier")
    mmr: int = Field(description="Skill rating / Elo")
    win_rate: float = Field(description="Win percentage")

    model_config = ConfigDict(from_attributes=True)


class BestSquadCompositionSchema(BaseModel):
    """The single optimal 5-player squad composition."""
    overall_score: float = Field(description="Weighted overall squad synergy score (0-100)")
    compatibility_score: float = Field(description="Average pairwise compatibility score across all 5 players")
    role_balance_score: float = Field(description="Tactical role coverage score (0-100)")
    skill_balance_score: float = Field(description="MMR balance and lobby parity score (0-100)")
    communication_score: float = Field(description="Squad-wide verbal coordination score (0-100)")
    leadership_score: float = Field(description="Command hierarchy clarity score (0-100)")
    designated_igl: str | None = Field(default=None, description="Designated In-Game Leader for the squad")
    mean_mmr: float = Field(description="Average squad skill rating")
    skill_variance: float = Field(description="Standard deviation of squad MMR")
    role_distribution: dict[str, int] = Field(description="Count of players per tactical role")
    missing_roles: list[str] = Field(default_factory=list, description="Roles not covered in the 5-player squad")
    members: list[BestSquadMemberSchema] = Field(description="The 5 squad members (including Current User)")
    synergy_reasons: list[str] = Field(default_factory=list, description="Key squad synergy rationales")

    model_config = ConfigDict(from_attributes=True)


class SquadRecommendationResponse(BaseModel):
    """Consolidated Squad Recommendation response output."""
    current_user_id: str = Field(description="UUID of requesting user")
    current_username: str = Field(description="Moniker of requesting user")
    top_10_teammates: list[TeammateCandidateSchema] = Field(description="Top 10 ranked individual candidates")
    best_5_player_squad: BestSquadCompositionSchema = Field(description="Best optimized 5-player squad composition")
    missing_roles: list[str] = Field(description="Missing tactical roles in best squad")
    confidence_score: float = Field(description="Algorithmic confidence score (0.0 to 1.0)")
    summary: str = Field(description="Human-readable synthesis of the recommendation")

    model_config = ConfigDict(from_attributes=True)


class SquadRecommendationRequest(BaseModel):
    """Request options for generating squad recommendations."""
    game_name: str = Field(default="Valorant", description="Target competitive game title")
    target_region: str | None = Field(default=None, description="Optional region filter")
    candidate_pool_limit: int = Field(default=40, ge=5, le=100, description="Max candidate pool size to analyze")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "game_name": "Valorant",
                "target_region": "NA-East",
                "candidate_pool_limit": 30,
            }
        }
    )
