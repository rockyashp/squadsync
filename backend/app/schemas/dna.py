"""
Pydantic v2 schemas for GamerDNA evaluation, classification results, and profile DNA.
"""

from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict, Field


class GamerDNABase(BaseModel):
    """Core psychometric traits and role classifications."""
    leadership: int = Field(..., ge=0, le=100, description="Leadership score 0-100")
    communication: int = Field(..., ge=0, le=100, description="Communication score 0-100")
    strategy: int = Field(..., ge=0, le=100, description="Strategy score 0-100")
    teamwork: int = Field(..., ge=0, le=100, description="Teamwork score 0-100")
    aggression: int = Field(..., ge=0, le=100, description="Aggression score 0-100")
    confidence: int = Field(default=50, ge=0, le=100, description="Confidence score 0-100")
    primary_role: str = Field(..., description="Dominant classified gamer role", examples=["Leader", "Strategist"])
    secondary_role: str | None = Field(None, description="Secondary complementary gamer role", examples=["Support"])
    personality: str = Field(..., description="Synthesized archetype profile", examples=["The Grandmaster Shotcaller"])
    reasoning: str | None = Field(None, description="Detailed rule-based classification justification")


class GamerDNARead(GamerDNABase):
    """Public representation of GamerDNA database record."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="Unique DNA record ID")
    user_id: uuid.UUID = Field(..., description="Associated User ID")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Record last updated timestamp")


class GamerDNAEvaluationResponse(BaseModel):
    """Comprehensive evaluation payload returned when GamerDNA is analyzed from survey."""
    primary_role: str = Field(..., description="Primary gamer role")
    secondary_role: str = Field(..., description="Secondary gamer role")
    personality: str = Field(..., description="Gamer archetype title")
    score_breakdown: dict[str, int] = Field(
        ...,
        description="Dimension scores across Leadership, Communication, Strategy, Teamwork, Aggression",
    )
    role_affinities: dict[str, float] = Field(
        ...,
        description="Affinities across all 6 roles (Leader, Support, Strategist, Duelist, Sentinel, Controller)",
    )
    reasoning: str = Field(..., description="Human-readable decision explanation")
    gamer_dna: GamerDNARead = Field(..., description="Persisted GamerDNA entity")


class ProfileCardSummary(BaseModel):
    """Profile attributes included in the Gamer DNA Card."""
    model_config = ConfigDict(from_attributes=True)

    full_name: str | None = Field(None, description="Gamer full name")
    avatar_url: str | None = Field(None, description="Avatar image URL")
    favorite_game: str | None = Field(None, description="Main game title")
    rank: str | None = Field(None, description="Competitive tier or rank")
    preferred_role: str | None = Field(None, description="Preferred gameplay role")
    region: str | None = Field(None, description="Gaming region/server")
    language: str | None = Field("en", description="Primary communication language")
    bio: str | None = Field(None, description="User biography")


class GamerDNACardResponse(BaseModel):
    """
    Frontend-optimized Gamer DNA Card representation.
    Synthesizes user identity, profile details, psychometrics, strengths, weaknesses, and playstyle.
    """
    username: str = Field(..., description="Gamer username", examples=["shadow_striker"])
    profile: ProfileCardSummary | None = Field(None, description="User gamer profile details if created")
    primary_role: str = Field(..., description="Primary classified gamer role", examples=["Leader"])
    secondary_role: str | None = Field(None, description="Secondary classified gamer role", examples=["Strategist"])
    leadership_score: int = Field(..., ge=0, le=100, description="Leadership trait score (0-100)")
    communication_score: int = Field(..., ge=0, le=100, description="Communication trait score (0-100)")
    strategy_score: int = Field(..., ge=0, le=100, description="Strategy trait score (0-100)")
    aggression_score: int = Field(..., ge=0, le=100, description="Aggression trait score (0-100)")
    teamwork_score: int = Field(..., ge=0, le=100, description="Teamwork trait score (0-100)")
    confidence_score: int = Field(default=50, ge=0, le=100, description="Confidence trait score (0-100)")
    personality: str = Field(..., description="Archetype title", examples=["The Grandmaster Shotcaller"])
    strengths: list[str] = Field(..., description="Key competitive strengths based on evaluated psychometrics")
    weaknesses: list[str] = Field(..., description="Areas for tactical improvement")
    recommended_playstyle: str = Field(..., description="Tailored gameplay guidance for optimal performance")
