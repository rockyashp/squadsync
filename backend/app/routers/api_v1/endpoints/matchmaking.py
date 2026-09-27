"""
FastAPI endpoints for Matchmaking & Squad Recommendation:
- POST /matchmaking/compatibility: Pairwise compatibility evaluation
- POST /matchmaking/recommend-squad: Algorithmic squad recommendation
- POST /matchmaking/evaluate-team: Team balance and missing roles evaluation
"""

from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser, MatchmakingServiceDep
from app.schemas.common import ApiResponse
from app.schemas.matchmaking import (
    CompatibilityResponse,
    PairwiseCompatibilityRequest,
    SquadComposition,
    SquadRecommendationRequest,
    SquadRecommendationResponse,
    TeamEvaluationRequest,
)

router = APIRouter()


@router.post(
    "/compatibility",
    response_model=ApiResponse[CompatibilityResponse],
    status_code=status.HTTP_200_OK,
    summary="Evaluate player compatibility",
    description=(
        "Calculates multi-dimensional compatibility between the authenticated player and a target user. "
        "Evaluates role synergy, communication match, skill alignment, schedule overlap, language, and region."
    ),
)
async def evaluate_player_compatibility(
    payload: PairwiseCompatibilityRequest,
    current_user: CurrentUser,
    matchmaking_service: MatchmakingServiceDep,
) -> ApiResponse[CompatibilityResponse]:
    """Calculate compatibility percentage, breakdown, reasons, and warnings between two players."""
    result = await matchmaking_service.calculate_player_compatibility(
        user_a_id=current_user.id,
        user_b_id=payload.target_user_id,
    )
    return ApiResponse.ok(
        data=result,
        message="Player compatibility evaluated successfully.",
    )


@router.post(
    "/recommend-squad",
    response_model=ApiResponse[SquadRecommendationResponse],
    status_code=status.HTTP_200_OK,
    summary="Recommend optimal squads",
    description=(
        "Uses heuristic combinatorial search to find the highest-chemistry squads for the player. "
        "Optimizes role diversity, archetype balance, skill parity, and communication match."
    ),
)
async def recommend_squads(
    payload: SquadRecommendationRequest,
    current_user: CurrentUser,
    matchmaking_service: MatchmakingServiceDep,
) -> ApiResponse[SquadRecommendationResponse]:
    """Generate recommended squads tailored to the requester's game, stats, and DNA."""
    result = await matchmaking_service.recommend_squads(
        user_id=current_user.id,
        game_name=payload.game_name,
        squad_size=payload.squad_size,
        candidate_pool_limit=payload.candidate_limit,
        target_region=payload.target_region,
    )
    return ApiResponse.ok(
        data=result,
        message="Recommended squads generated successfully.",
    )


@router.post(
    "/evaluate-team",
    response_model=ApiResponse[SquadComposition],
    status_code=status.HTTP_200_OK,
    summary="Evaluate existing team composition",
    description=(
        "Analyzes an existing roster of 2-5 players: computes team balance %, identifies missing roles, "
        "measures skill variance (MMR spread), and generates tactical strengths and warnings."
    ),
)
async def evaluate_team(
    payload: TeamEvaluationRequest,
    current_user: CurrentUser,
    matchmaking_service: MatchmakingServiceDep,
) -> ApiResponse[SquadComposition]:
    """Evaluate full team balance, missing roles, and warnings for specified player IDs."""
    result = await matchmaking_service.evaluate_team(
        user_ids=payload.user_ids,
        game_name=payload.game_name,
    )
    return ApiResponse.ok(
        data=result,
        message="Team composition evaluated successfully.",
    )
