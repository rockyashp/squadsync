"""
Squad Recommendation API endpoints.
Provides authenticated squad recommendations querying database candidates
and standalone evaluation for candidate pools.
"""

from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser, SquadRecommendationServiceDep
from app.schemas.common import ApiResponse
from app.schemas.squad_recommendation import (
    BestSquadCompositionSchema,
    BestSquadMemberSchema,
    SquadRecommendationRequest,
    SquadRecommendationResponse,
    TeammateCandidateSchema,
)

router = APIRouter()


def _format_recommendation_response(result) -> SquadRecommendationResponse:
    """Helper converting internal SquadRecommendationResult to Pydantic SquadRecommendationResponse."""
    top_10 = [
        TeammateCandidateSchema(
            user_id=str(t.user_id),
            username=t.username,
            compatibility_score=t.compatibility_score,
            primary_role=t.primary_role,
            secondary_role=t.secondary_role,
            rank=t.rank or "Unranked",
            mmr=t.mmr,
            win_rate=t.win_rate,
            personality=t.personality,
            synergy_highlights=t.synergy_highlights,
        )
        for t in result.top_10_teammates
    ]

    best_squad = result.best_5_player_squad
    squad_members = [
        BestSquadMemberSchema(
            user_id=str(m.user_id),
            username=m.username,
            primary_role=m.primary_role,
            secondary_role=m.secondary_role,
            rank=m.rank or "Unranked",
            mmr=m.mmr,
            win_rate=m.win_rate,
        )
        for m in best_squad.members
    ]

    best_squad_schema = BestSquadCompositionSchema(
        overall_score=best_squad.overall_score,
        compatibility_score=best_squad.compatibility_score,
        role_balance_score=best_squad.role_balance_score,
        skill_balance_score=best_squad.skill_balance_score,
        communication_score=best_squad.communication_score,
        leadership_score=best_squad.leadership_score,
        designated_igl=best_squad.designated_igl,
        mean_mmr=best_squad.mean_mmr,
        skill_variance=best_squad.skill_variance,
        role_distribution=best_squad.role_distribution,
        missing_roles=best_squad.missing_roles,
        members=squad_members,
        synergy_reasons=best_squad.synergy_reasons,
    )

    return SquadRecommendationResponse(
        current_user_id=str(result.current_user.user_id),
        current_username=result.current_user.username,
        top_10_teammates=top_10,
        best_5_player_squad=best_squad_schema,
        missing_roles=result.missing_roles,
        confidence_score=result.confidence_score,
        summary=result.summary,
    )


@router.post(
    "/recommend",
    response_model=ApiResponse[SquadRecommendationResponse],
    status_code=status.HTTP_200_OK,
    summary="Generate Squad Recommendation for Authenticated User",
    description=(
        "Calculates Compatibility, Role Balance, Skill Balance, Communication, and Leadership Distribution "
        "across database candidates. Generates Top 10 Teammates, the Best 5-player squad containing Current User, "
        "detects Missing Roles, and computes an algorithmic Confidence Score."
    ),
)
async def generate_squad_recommendation(
    request: SquadRecommendationRequest,
    current_user: CurrentUser,
    squad_service: SquadRecommendationServiceDep,
) -> ApiResponse[SquadRecommendationResponse]:
    """Generates optimal 5-player squad and top 10 teammates for current user."""
    result = await squad_service.recommend_for_user(
        user_id=current_user.id,
        game_name=request.game_name,
        target_region=request.target_region,
        pool_limit=request.candidate_pool_limit,
    )
    return ApiResponse.ok(
        data=_format_recommendation_response(result),
        message="Squad recommendation generated successfully.",
    )
