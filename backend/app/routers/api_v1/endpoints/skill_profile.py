"""
Skill Profile API endpoints.
Provides decoupled inference evaluation, live skill profile inspection,
and on-demand generation with database persistence.
"""

from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser, SkillProfileServiceDep
from app.schemas.common import ApiResponse
from app.schemas.skill_profile import (
    SkillDimensionDetail,
    SkillProfileEvaluateRequest,
    SkillProfileResponse,
)

router = APIRouter()


def _to_response_dto(result) -> SkillProfileResponse:
    """Helper converting internal SkillProfileResult to Pydantic SkillProfileResponse."""
    return SkillProfileResponse(
        overall_score=result.overall_score,
        overall_tier=result.overall_tier,
        mechanical_skill=SkillDimensionDetail(
            name=result.mechanical_skill.name,
            score=result.mechanical_skill.score,
            tier=result.mechanical_skill.tier,
            explanation=result.mechanical_skill.explanation,
            signal_breakdown=result.mechanical_skill.signal_breakdown,
        ),
        communication=SkillDimensionDetail(
            name=result.communication.name,
            score=result.communication.score,
            tier=result.communication.tier,
            explanation=result.communication.explanation,
            signal_breakdown=result.communication.signal_breakdown,
        ),
        leadership=SkillDimensionDetail(
            name=result.leadership.name,
            score=result.leadership.score,
            tier=result.leadership.tier,
            explanation=result.leadership.explanation,
            signal_breakdown=result.leadership.signal_breakdown,
        ),
        consistency=SkillDimensionDetail(
            name=result.consistency.name,
            score=result.consistency.score,
            tier=result.consistency.tier,
            explanation=result.consistency.explanation,
            signal_breakdown=result.consistency.signal_breakdown,
        ),
        decision_making=SkillDimensionDetail(
            name=result.decision_making.name,
            score=result.decision_making.score,
            tier=result.decision_making.tier,
            explanation=result.decision_making.explanation,
            signal_breakdown=result.decision_making.signal_breakdown,
        ),
        game_sense=SkillDimensionDetail(
            name=result.game_sense.name,
            score=result.game_sense.score,
            tier=result.game_sense.tier,
            explanation=result.game_sense.explanation,
            signal_breakdown=result.game_sense.signal_breakdown,
        ),
        radar_chart=result.radar_chart,
        top_strengths=result.top_strengths,
        growth_areas=result.growth_areas,
    )


@router.post(
    "/evaluate",
    response_model=ApiResponse[SkillProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Evaluate Skill Profile on Input Payload",
    description=(
        "Computes the 6 competitive skill dimensions (Mechanical Skill, Communication, "
        "Leadership, Consistency, Decision Making, Game Sense) from an arbitrary payload "
        "of Gamer DNA psychometrics and official telemetry, including full score explanations."
    ),
)
async def evaluate_skill_profile(
    request: SkillProfileEvaluateRequest,
    skill_service: SkillProfileServiceDep,
) -> ApiResponse[SkillProfileResponse]:
    """Evaluates skill profile without requiring database lookup."""
    result = skill_service.evaluate_payload(request)
    return ApiResponse.ok(
        data=_to_response_dto(result),
        message="Skill profile evaluated successfully.",
    )


@router.get(
    "/me",
    response_model=ApiResponse[SkillProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Current User Skill Profile",
    description="Calculates and returns the 6-dimensional skill profile for the authenticated user.",
)
async def get_my_skill_profile(
    current_user: CurrentUser,
    skill_service: SkillProfileServiceDep,
) -> ApiResponse[SkillProfileResponse]:
    """Retrieves computed skill profile for the current user."""
    result = await skill_service.generate_for_user(user_id=current_user.id, persist=False)
    return ApiResponse.ok(
        data=_to_response_dto(result),
        message="User skill profile retrieved successfully.",
    )


@router.post(
    "/generate",
    response_model=ApiResponse[SkillProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Generate and Persist User Skill Profile",
    description=(
        "Fuses the authenticated user's stored Gamer DNA, survey answers, and cross-game "
        "telemetry to generate and persist the competitive skill profile into the database."
    ),
)
async def generate_my_skill_profile(
    current_user: CurrentUser,
    skill_service: SkillProfileServiceDep,
) -> ApiResponse[SkillProfileResponse]:
    """Generates and saves the competitive skill profile for current user."""
    result = await skill_service.generate_for_user(user_id=current_user.id, persist=True)
    return ApiResponse.ok(
        data=_to_response_dto(result),
        message="User skill profile generated and saved successfully.",
    )
