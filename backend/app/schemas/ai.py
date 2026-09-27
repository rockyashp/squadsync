"""
Pydantic v2 schemas for the unified FastAPI AI Module.
Defines standardized data contracts for the 7 consolidated AI endpoints:
- GET /dna/me
- GET /role/me
- GET /skill-profile
- GET /compatibility/{user_id}
- GET /recommendations
- GET /squad
- GET /explanation/{user_id}
"""

from typing import Any
import uuid
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.compatibility import CompatibilityReportResponse
from app.schemas.dna import GamerDNACardResponse
from app.schemas.explanation import ExplanationResponse
from app.schemas.role_classifier import RoleClassificationResponse
from app.schemas.skill_profile import SkillProfileResponse
from app.schemas.squad_recommendation import BestSquadCompositionSchema, TeammateCandidateSchema


class GamerDNAMeResponse(BaseModel):
    """Gamer DNA profile response contract."""
    dna: GamerDNACardResponse = Field(description="The gamer psychometric DNA profile card")

    model_config = ConfigDict(from_attributes=True)


class RoleClassificationMeResponse(BaseModel):
    """AI Role classification response contract."""
    classification: RoleClassificationResponse = Field(description="Role classification details and reasoning")

    model_config = ConfigDict(from_attributes=True)


class SkillProfileMeResponse(BaseModel):
    """AI Skill Profile generator response contract."""
    skill_profile: SkillProfileResponse = Field(description="Six-axis skill evaluations and narrative explanations")

    model_config = ConfigDict(from_attributes=True)


class CompatibilityMeResponse(BaseModel):
    """Pairwise AI Compatibility report response contract."""
    compatibility: CompatibilityReportResponse = Field(description="Pairwise compatibility breakdown and duo tier")

    model_config = ConfigDict(from_attributes=True)


class RecommendationsMeResponse(BaseModel):
    """Top 10 recommended teammates response contract."""
    current_user_id: str = Field(description="Requesting user UUID")
    target_game: str = Field(description="Target game title")
    top_teammates: list[TeammateCandidateSchema] = Field(description="Top ranked individual teammates")

    model_config = ConfigDict(from_attributes=True)


class SquadMeResponse(BaseModel):
    """Best 5-player squad composition response contract."""
    current_user_id: str = Field(description="Requesting user UUID")
    target_game: str = Field(description="Target game title")
    squad: BestSquadCompositionSchema = Field(description="Optimal 5-player squad composition")
    missing_roles: list[str] = Field(default_factory=list, description="Unfilled tactical roles")
    confidence_score: float = Field(description="Algorithmic confidence score (0.0 to 1.0)")

    model_config = ConfigDict(from_attributes=True)


class ExplanationMeResponse(BaseModel):
    """Natural language compatibility explanation response contract."""
    explanation: ExplanationResponse = Field(description="Structured human-readable explanation and coaching tips")

    model_config = ConfigDict(from_attributes=True)
