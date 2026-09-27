"""
Pydantic v2 schemas for Matchmaking Engine:
- Candidate profiles (Stats, Survey, DNA, Region, Language, Schedule, Games)
- Pairwise compatibility breakdowns, reasons, and warnings
- Squad composition, team balance, missing roles, and recommendations
- Team evaluation payloads
"""

from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict, Field


class MatchmakingCandidate(BaseModel):
    """
    Standardized feature profile representing a player ready for matchmaking.
    Combines Official Stats, Survey Dimensions, Gamer DNA, and Profile Attributes.
    """
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    username: str
    display_name: str | None = None
    avatar_url: str | None = None

    # 1. Official Game Telemetry
    rank: str | None = None
    mmr: int = 1500
    win_rate: float = 50.0       # 0.0 - 100.0%
    matches_played: int = 0
    kd_ratio: float = 1.0

    # 2. Survey Psychometrics (0 - 100)
    leadership: int = 50
    communication: int = 50
    strategy: int = 50
    teamwork: int = 50
    aggression: int = 50
    confidence: int = 50

    # 3. Gamer DNA Archetypes & Affinities
    primary_role: str = "Flex"
    secondary_role: str | None = None
    personality: str = "The Adaptive Competitor"
    role_affinities: dict[str, float] = Field(default_factory=dict)

    # 4. Regional & Social Parameters
    region: str = "NA-East"
    languages: list[str] = Field(default_factory=lambda: ["en"])
    schedule_tags: list[str] = Field(default_factory=lambda: ["evenings"])
    preferred_games: list[str] = Field(default_factory=lambda: ["Valorant"])
    preferred_roles: list[str] = Field(default_factory=list)


class PairwiseCompatibilityBreakdown(BaseModel):
    """Granular metric breakdown of compatibility between two players."""
    role_synergy: float = Field(..., ge=0, le=100, description="Synergy between roles and traits (0-100)")
    communication_match: float = Field(..., ge=0, le=100, description="Communication score and style alignment")
    skill_alignment: float = Field(..., ge=0, le=100, description="Parity in rank and MMR (0-100)")
    schedule_overlap: float = Field(..., ge=0, le=100, description="Compatibility of availability windows (0-100)")
    language_match: float = Field(..., ge=0, le=100, description="Common language alignment (0-100)")
    region_match: float = Field(..., ge=0, le=100, description="Server latency and ping compatibility (0-100)")
    game_match: float = Field(..., ge=0, le=100, description="Shared preferred games overlap (0-100)")


class CompatibilityResponse(BaseModel):
    """Complete pairwise compatibility evaluation payload."""
    player_a_id: uuid.UUID
    player_b_id: uuid.UUID
    player_a_username: str
    player_b_username: str
    overall_compatibility_pct: float = Field(..., ge=0, le=100, description="Composite compatibility rating %")
    breakdown: PairwiseCompatibilityBreakdown
    reasons: list[str] = Field(..., description="Tactical justifications supporting compatibility")
    warnings: list[str] = Field(default_factory=list, description="Potential friction or disparity alerts")


class SquadMember(BaseModel):
    """Player representation within a formed squad."""
    user_id: uuid.UUID
    username: str
    assigned_role: str
    primary_role: str
    secondary_role: str | None = None
    rank: str | None = None
    mmr: int = 1500
    win_rate: float = 50.0
    personality: str


class SquadComposition(BaseModel):
    """Complete evaluation and composition of a recommended or existing squad."""
    squad_size: int
    game_name: str
    members: list[SquadMember]
    compatibility_pct: float = Field(..., ge=0, le=100, description="Overall squad synergy rating %")
    team_balance_pct: float = Field(..., ge=0, le=100, description="Role distribution and archetype balance %")
    communication_match_pct: float = Field(..., ge=0, le=100, description="Squad communication harmony %")
    skill_variance: float = Field(..., description="Standard deviation of MMR across squad members")
    role_distribution: dict[str, int] = Field(..., description="Counts of each role represented")
    missing_roles: list[str] = Field(default_factory=list, description="Essential archetypes not filled")
    reasons: list[str] = Field(..., description="Core strengths of this squad composition")
    warnings: list[str] = Field(default_factory=list, description="Tactical gaps or imbalances to be aware of")


class SquadRecommendationRequest(BaseModel):
    """Parameters for squad recommendation search."""
    game_name: str = Field(default="Valorant", description="Target competitive title")
    squad_size: int = Field(default=5, ge=2, le=5, description="Target squad size (default 5)")
    target_region: str | None = Field(None, description="Optional region filter (e.g. 'NA-East')")
    max_rank_difference: int | None = Field(None, description="Optional maximum allowed MMR delta")
    candidate_limit: int = Field(default=30, ge=5, le=100, description="Candidate pool size to inspect")


class SquadRecommendationResponse(BaseModel):
    """Collection of top ranked squads tailored for the requester."""
    requesting_user_id: uuid.UUID
    game_name: str
    top_squads: list[SquadComposition]
    total_candidates_analyzed: int


class TeamEvaluationRequest(BaseModel):
    """Payload for evaluating an existing group of players."""
    user_ids: list[uuid.UUID] = Field(..., min_length=2, max_length=5, description="Member UUIDs")
    game_name: str = Field(default="Valorant", description="Target competitive game title")


class PairwiseCompatibilityRequest(BaseModel):
    """Payload for evaluating compatibility between current user and target user."""
    target_user_id: uuid.UUID
    game_name: str = Field(default="Valorant", description="Target game for skill comparison")
