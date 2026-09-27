"""
FastAPI AI Core Module endpoints.
Consolidated router exposing the platform's unified AI capabilities:
- GET /dna/me
- GET /role/me
- GET /skill-profile
- GET /compatibility/{user_id}
- GET /recommendations
- GET /squad
- GET /explanation/{user_id}
"""

import uuid
from fastapi import APIRouter, Query, status

from app.core.dependencies import AIServiceDep, CurrentUser
from app.schemas.ai import (
    CompatibilityMeResponse,
    ExplanationMeResponse,
    GamerDNAMeResponse,
    RecommendationsMeResponse,
    RoleClassificationMeResponse,
    SkillProfileMeResponse,
    SquadMeResponse,
)
from app.schemas.common import ApiResponse

router = APIRouter()


@router.get(
    "/dna/me",
    response_model=ApiResponse[GamerDNAMeResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Authenticated User Gamer DNA",
    description="Retrieves the psychometric Gamer DNA profile, trait scores, and personality archetype for the authenticated user.",
)
async def get_my_gamer_dna(
    current_user: CurrentUser,
    ai_service: AIServiceDep,
) -> ApiResponse[GamerDNAMeResponse]:
    """Retrieves current user's Gamer DNA."""
    data = await ai_service.get_my_dna(user=current_user)
    return ApiResponse.ok(data=data, message="Gamer DNA retrieved successfully.")


@router.get(
    "/role/me",
    response_model=ApiResponse[RoleClassificationMeResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Authenticated User AI Role Classification",
    description="Generates dynamic AI Role Classification (Primary, Secondary, Confidence, Reasoning) based on DNA, stats, and preferences.",
)
async def get_my_role_classification(
    current_user: CurrentUser,
    ai_service: AIServiceDep,
) -> ApiResponse[RoleClassificationMeResponse]:
    """Generates AI Role classification for current user."""
    data = await ai_service.get_my_role(user_id=current_user.id)
    return ApiResponse.ok(data=data, message="Role classification generated successfully.")


@router.get(
    "/skill-profile",
    response_model=ApiResponse[SkillProfileMeResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Authenticated User AI Skill Profile",
    description="Generates comprehensive Six-Axis AI Skill Profile (Mechanical, Comms, Leadership, Consistency, Decision Making, Game Sense) with granular explanations.",
)
async def get_my_skill_profile(
    current_user: CurrentUser,
    ai_service: AIServiceDep,
) -> ApiResponse[SkillProfileMeResponse]:
    """Generates six-axis skill profile for current user."""
    data = await ai_service.get_my_skill_profile(user_id=current_user.id)
    return ApiResponse.ok(data=data, message="Skill profile generated successfully.")


@router.get(
    "/compatibility/{user_id}",
    response_model=ApiResponse[CompatibilityMeResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Pairwise AI Compatibility with Target User",
    description="Calculates 10-dimensional pairwise compatibility score, duo tier, strengths, weaknesses, recommendations, and risk factors.",
)
async def get_compatibility_with_target_user(
    user_id: uuid.UUID,
    current_user: CurrentUser,
    ai_service: AIServiceDep,
) -> ApiResponse[CompatibilityMeResponse]:
    """Calculates pairwise compatibility with target user."""
    data = await ai_service.get_compatibility_with_user(
        current_user_id=current_user.id,
        target_user_id=user_id,
    )
    return ApiResponse.ok(data=data, message="Compatibility analysis generated successfully.")


@router.get(
    "/recommendations",
    response_model=ApiResponse[RecommendationsMeResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Top Recommended Teammates",
    description="Retrieves Top 10 individual recommended teammates ranked by synergy, compatibility score, roles, and ranks.",
)
async def get_teammate_recommendations(
    current_user: CurrentUser,
    ai_service: AIServiceDep,
    game: str = Query(default="Valorant", description="Target game title"),
    limit: int = Query(default=40, ge=5, le=100, description="Candidate search pool size"),
) -> ApiResponse[RecommendationsMeResponse]:
    """Retrieves top 10 recommended teammates for current user."""
    data = await ai_service.get_teammate_recommendations(
        user_id=current_user.id,
        game_name=game,
        limit=limit,
    )
    return ApiResponse.ok(data=data, message="Teammate recommendations retrieved successfully.")


@router.get(
    "/squad",
    response_model=ApiResponse[SquadMeResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Optimal 5-Player Squad Composition",
    description="Computes the single best 5-player squad composition containing the authenticated user, role balance, skill parity, and designated IGL.",
)
async def get_optimal_squad(
    current_user: CurrentUser,
    ai_service: AIServiceDep,
    game: str = Query(default="Valorant", description="Target game title"),
    limit: int = Query(default=40, ge=5, le=100, description="Candidate search pool size"),
) -> ApiResponse[SquadMeResponse]:
    """Computes optimal 5-player squad composition containing current user."""
    data = await ai_service.get_optimal_squad(
        user_id=current_user.id,
        game_name=game,
        limit=limit,
    )
    return ApiResponse.ok(data=data, message="Optimal squad composition generated successfully.")


@router.get(
    "/explanation/{user_id}",
    response_model=ApiResponse[ExplanationMeResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Natural Language Compatibility Explanation with Target User",
    description="Generates structured template-based natural language explanation answering why two players match, why they don't match, strengths, weaknesses, and improvement suggestions.",
)
async def get_explanation_with_target_user(
    user_id: uuid.UUID,
    current_user: CurrentUser,
    ai_service: AIServiceDep,
) -> ApiResponse[ExplanationMeResponse]:
    """Generates natural language explanation and coaching tips with target user."""
    data = await ai_service.get_explanation_with_user(
        current_user_id=current_user.id,
        target_user_id=user_id,
    )
    return ApiResponse.ok(data=data, message="Compatibility explanation generated successfully.")
