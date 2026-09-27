"""
AI Explanation Engine API endpoints.
Provides human-readable natural language explanations of player compatibility,
synthesizing Gamer DNA, tactical Roles, and official Statistics using template-based NLG.
"""

import uuid
from fastapi import APIRouter, status

from app.core.dependencies import AIExplanationServiceDep, CurrentUser
from app.schemas.common import ApiResponse
from app.schemas.explanation import ExplanationCompareRequest, ExplanationResponse

router = APIRouter()


@router.post(
    "/compare",
    response_model=ApiResponse[ExplanationResponse],
    status_code=status.HTTP_200_OK,
    summary="Generate Compatibility Explanation from Payload",
    description=(
        "Translates psychometrics (Gamer DNA), tactical roles, and competitive telemetry "
        "into structured, human-readable explanations answering why two players match, "
        "why they don't match, their strengths, weaknesses, and improvement suggestions."
    ),
)
async def explain_compatibility_payload(
    request: ExplanationCompareRequest,
    explanation_service: AIExplanationServiceDep,
) -> ApiResponse[ExplanationResponse]:
    """Generates natural language compatibility explanation for arbitrary player profiles."""
    result = explanation_service.explain_payload(request)
    return ApiResponse.ok(
        data=result,
        message="Compatibility explanation generated successfully.",
    )


@router.get(
    "/users/{target_user_id}",
    response_model=ApiResponse[ExplanationResponse],
    status_code=status.HTTP_200_OK,
    summary="Generate Compatibility Explanation between Authenticated User and Target User",
    description=(
        "Hydrates Gamer DNA, Profile preferences, and official competitive statistics "
        "for both the authenticated user and the target user from the database, "
        "and produces a comprehensive human-readable compatibility explanation."
    ),
)
async def explain_compatibility_with_user(
    target_user_id: uuid.UUID,
    current_user: CurrentUser,
    explanation_service: AIExplanationServiceDep,
) -> ApiResponse[ExplanationResponse]:
    """Generates natural language compatibility explanation between current user and target user."""
    result = await explanation_service.explain_between_users(
        user_a_id=current_user.id,
        user_b_id=target_user_id,
    )
    return ApiResponse.ok(
        data=result,
        message="Compatibility explanation generated successfully.",
    )
