"""
AI Compatibility API endpoints.
Provides decoupled pairwise player comparison and live user-to-user synergy analysis.
"""

import uuid
from fastapi import APIRouter, status

from app.core.dependencies import AICompatibilityServiceDep, CurrentUser
from app.schemas.common import ApiResponse
from app.schemas.compatibility import (
    CompatibilityCompareRequest,
    CompatibilityReportResponse,
)

router = APIRouter()


@router.post(
    "/compare",
    response_model=ApiResponse[CompatibilityReportResponse],
    status_code=status.HTTP_200_OK,
    summary="Compare Two Players with AI Compatibility Engine",
    description=(
        "Compares Player A and Player B across 10 dimensions: Leadership, Communication, "
        "Aggression, Strategy, Region, Language, Schedule, Official Rank, Win Rate, and Preferred Role. "
        "Outputs a weighted Compatibility Score, Duo Tier, Strengths, Weaknesses, Recommendations, "
        "and Risk Factors."
    ),
)
async def compare_players_compatibility(
    request: CompatibilityCompareRequest,
    compatibility_service: AICompatibilityServiceDep,
) -> ApiResponse[CompatibilityReportResponse]:
    """Compares two players directly from the provided payload."""
    report = compatibility_service.compare_payload(request)
    response_data = CompatibilityReportResponse(
        player_a_name=report.player_a_name,
        player_b_name=report.player_b_name,
        compatibility_score=report.compatibility_score,
        tier=report.tier,
        dimension_scores=report.dimension_scores,
        strengths=report.strengths,
        weaknesses=report.weaknesses,
        recommendations=report.recommendations,
        risk_factors=report.risk_factors,
    )
    return ApiResponse.ok(
        data=response_data,
        message="Player compatibility evaluated successfully.",
    )


@router.get(
    "/compare/{target_user_id}",
    response_model=ApiResponse[CompatibilityReportResponse],
    status_code=status.HTTP_200_OK,
    summary="Compare Current User with Target User",
    description=(
        "Gathers database profiles, Gamer DNA, and telemetry for the authenticated user and the "
        "specified target user to generate their pairwise AI compatibility report."
    ),
)
async def compare_with_user(
    target_user_id: uuid.UUID,
    current_user: CurrentUser,
    compatibility_service: AICompatibilityServiceDep,
) -> ApiResponse[CompatibilityReportResponse]:
    """Compares the current authenticated user with another user by user ID."""
    report = await compatibility_service.compare_users(
        user_a_id=current_user.id,
        user_b_id=target_user_id,
    )
    response_data = CompatibilityReportResponse(
        player_a_name=report.player_a_name,
        player_b_name=report.player_b_name,
        compatibility_score=report.compatibility_score,
        tier=report.tier,
        dimension_scores=report.dimension_scores,
        strengths=report.strengths,
        weaknesses=report.weaknesses,
        recommendations=report.recommendations,
        risk_factors=report.risk_factors,
    )
    return ApiResponse.ok(
        data=response_data,
        message=f"Compatibility between {report.player_a_name} and {report.player_b_name} evaluated successfully.",
    )
