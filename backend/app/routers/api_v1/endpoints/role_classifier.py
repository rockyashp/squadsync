"""
Gamer Role Classification API endpoints.
Provides decoupled inference evaluation, user-profile classification,
and engine configuration inspection.
"""

from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser, RoleClassifierServiceDep
from app.schemas.common import ApiResponse
from app.schemas.role_classifier import (
    RoleClassificationResponse,
    RoleClassifierConfigResponse,
    RoleClassifierEvaluateRequest,
)

router = APIRouter()


@router.post(
    "/evaluate",
    response_model=ApiResponse[RoleClassificationResponse],
    status_code=status.HTTP_200_OK,
    summary="Evaluate Gamer Role Classification",
    description=(
        "Executes multi-signal rule-based classification (easily swappable with ML) "
        "across the 4 core inputs:\n"
        "1. Gamer DNA psychometric feature vector\n"
        "2. Official game statistics (telemetry, KD, win rate, headshot %)\n"
        "3. Preferred tactical roles\n"
        "4. Preferred games and agent/hero affinities\n\n"
        "Returns Primary Role, Secondary Role, Confidence Score, and Explainable AI Reasoning."
    ),
)
async def evaluate_role_classification(
    request: RoleClassifierEvaluateRequest,
    classifier_service: RoleClassifierServiceDep,
) -> ApiResponse[RoleClassificationResponse]:
    """Evaluates role classification on the provided 4-signal feature payload."""
    result = classifier_service.evaluate_payload(request)
    response_data = RoleClassificationResponse(
        primary_role=result.primary_role,
        secondary_role=result.secondary_role,
        confidence_score=result.confidence_score,
        reasoning=result.reasoning,
        personality=result.personality,
        role_affinities=result.role_affinities,
        signal_contributions=result.signal_contributions,
        feature_importance=result.feature_importance,
    )
    return ApiResponse.ok(
        data=response_data,
        message="Gamer role evaluated successfully.",
    )


@router.post(
    "/me",
    response_model=ApiResponse[RoleClassificationResponse],
    status_code=status.HTTP_200_OK,
    summary="Classify Current User Roles from Telemetry and Profile",
    description=(
        "Aggregates the authenticated user's stored Gamer DNA, cross-game official telemetry, "
        "and profile preferences, executes the classification engine, persists the results into the "
        "gamer_dna table with confidence scoring, and returns the full evaluation."
    ),
)
async def classify_current_user_roles(
    current_user: CurrentUser,
    classifier_service: RoleClassifierServiceDep,
) -> ApiResponse[RoleClassificationResponse]:
    """Classifies roles for the authenticated user and persists results."""
    result = await classifier_service.evaluate_user(user_id=current_user.id, persist=True)
    response_data = RoleClassificationResponse(
        primary_role=result.primary_role,
        secondary_role=result.secondary_role,
        confidence_score=result.confidence_score,
        reasoning=result.reasoning,
        personality=result.personality,
        role_affinities=result.role_affinities,
        signal_contributions=result.signal_contributions,
        feature_importance=result.feature_importance,
    )
    return ApiResponse.ok(
        data=response_data,
        message="User gamer role classified and saved successfully.",
    )


@router.get(
    "/config",
    response_model=ApiResponse[RoleClassifierConfigResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Role Classifier Configuration",
    description="Returns active signal weights, role descriptions, and normalization benchmarks.",
)
async def get_classifier_configuration(
    classifier_service: RoleClassifierServiceDep,
) -> ApiResponse[RoleClassifierConfigResponse]:
    """Retrieves current classification engine configuration parameters."""
    config_data = classifier_service.get_config_metadata()
    return ApiResponse.ok(
        data=config_data,
        message="Classifier configuration retrieved successfully.",
    )
