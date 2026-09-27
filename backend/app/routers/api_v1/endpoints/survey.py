"""
Gamer DNA Survey API routes: Questions catalog, Submission, and Answer history.
Clean architecture implementation returning unified ApiResponse envelopes.
"""

from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser, SurveyServiceDep
from app.schemas.common import ApiResponse
from app.schemas.survey import (
    SurveyQuestionPublic,
    SurveyResponseRead,
    SurveySubmissionRequest,
    SurveySubmissionResult,
)

router = APIRouter()


@router.get(
    "/questions",
    response_model=ApiResponse[list[SurveyQuestionPublic]],
    status_code=status.HTTP_200_OK,
    summary="Get 20 Gamer DNA survey questions",
    description=(
        "Retrieves the complete set of 20 behavioral survey questions across 6 dimensions: "
        "Leadership, Communication, Strategy, Aggression, Teamwork, and Confidence. "
        "Scoring weights and evaluation formulas are strictly omitted to protect algorithmic integrity."
    ),
)
async def get_survey_questions(
    survey_service: SurveyServiceDep,
) -> ApiResponse[list[SurveyQuestionPublic]]:
    """Retrieve 20 behavioral questions with multiple choice options, excluding scoring weights."""
    questions = survey_service.get_public_questions()
    return ApiResponse.ok(
        data=questions,
        message="20 behavioral survey questions retrieved successfully.",
    )


@router.post(
    "",
    response_model=ApiResponse[SurveySubmissionResult],
    status_code=status.HTTP_201_CREATED,
    summary="Submit Gamer DNA survey answers",
    description=(
        "Submits selected choices for behavioral questions. "
        "Stores every answer separately in the database and computes category scores across all 6 dimensions."
    ),
)
@router.post(
    "/submit",
    response_model=ApiResponse[SurveySubmissionResult],
    status_code=status.HTTP_201_CREATED,
    summary="Submit survey answers (alias)",
    include_in_schema=False,
)
async def submit_survey(
    payload: SurveySubmissionRequest,
    current_user: CurrentUser,
    survey_service: SurveyServiceDep,
) -> ApiResponse[SurveySubmissionResult]:
    """Submit answers to be evaluated server-side and persisted individually."""
    result = await survey_service.submit_survey(
        user_id=current_user.id,
        submission=payload,
    )
    return ApiResponse.ok(
        data=result,
        message="Survey answers recorded and Gamer DNA classified successfully.",
    )


@router.get(
    "/history",
    response_model=ApiResponse[list[SurveyResponseRead]],
    status_code=status.HTTP_200_OK,
    summary="Get user survey response history",
    description="Fetches all individually saved survey answers recorded for the authenticated user.",
)
async def get_survey_history(
    current_user: CurrentUser,
    survey_service: SurveyServiceDep,
) -> ApiResponse[list[SurveyResponseRead]]:
    """Fetch all individually stored question answers for current user."""
    history = await survey_service.get_user_history(user_id=current_user.id)
    return ApiResponse.ok(
        data=history,
        message="Survey answer history retrieved successfully.",
    )
