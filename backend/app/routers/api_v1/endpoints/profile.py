"""
GamerProfile API routes: Create, Read, and Update profiles for authenticated users.
Clean architecture implementation returning unified ApiResponse envelopes.
"""

from fastapi import APIRouter, Body, status

from app.core.dependencies import CurrentUser, ProfileServiceDep
from app.schemas.common import ApiResponse
from app.schemas.profile import (
    GamerProfileCreate,
    GamerProfileRead,
    GamerProfileUpdate,
)

router = APIRouter()


@router.post(
    "",
    response_model=ApiResponse[GamerProfileRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create Gamer Profile",
    description=(
        "Initializes and saves a new gamer profile for the authenticated user. "
        "Allows setting display name, bio, server region, communication language, "
        "preferred games, preferred roles, availability schedule, and avatar URL. "
        "Raises 409 Conflict if a profile has already been initialized."
    ),
    responses={
        201: {"description": "Gamer profile successfully initialized"},
        401: {"description": "Authentication required"},
        409: {"description": "Profile already exists for this account"},
        422: {"description": "Validation error on input attributes"},
    },
)
async def create_my_profile(
    current_user: CurrentUser,
    profile_service: ProfileServiceDep,
    payload: GamerProfileCreate = Body(
        ...,
        openapi_examples={
            "standard_profile": {
                "summary": "Standard Gamer Profile",
                "value": {
                    "display_name": "ShadowStrike",
                    "bio": "Competitive FPS shotcaller and duelist main. Looking for high-immortal scrim teams.",
                    "region": "NA-East",
                    "language": "English",
                    "preferred_games": ["Valorant", "CS2", "Apex Legends"],
                    "preferred_roles": ["Duelist", "Initiator"],
                    "availability": "Weekdays 8PM - 12AM EST, Weekends anytime",
                    "avatar": "https://cdn.squadsync.gg/avatars/shadow.png",
                },
            }
        },
    ),
) -> ApiResponse[GamerProfileRead]:
    """Create a new gamer profile for the currently authenticated user."""
    profile = await profile_service.create_profile(
        user_id=current_user.id,
        profile_in=payload,
    )
    return ApiResponse.ok(
        data=GamerProfileRead.model_validate(profile),
        message="Gamer profile created successfully.",
    )


@router.get(
    "/me",
    response_model=ApiResponse[GamerProfileRead],
    status_code=status.HTTP_200_OK,
    summary="Get My Gamer Profile",
    description=(
        "Retrieves the complete gamer profile for the currently authenticated user. "
        "Returns 404 Not Found if the user has not yet initialized their profile."
    ),
    responses={
        200: {"description": "Gamer profile retrieved successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Gamer profile not yet created for this user"},
    },
)
async def get_my_profile(
    current_user: CurrentUser,
    profile_service: ProfileServiceDep,
) -> ApiResponse[GamerProfileRead]:
    """Retrieve profile for the currently authenticated user."""
    profile = await profile_service.get_by_user_id_or_404(current_user.id)
    return ApiResponse.ok(
        data=GamerProfileRead.model_validate(profile),
        message="Gamer profile retrieved successfully.",
    )


@router.put(
    "/me",
    response_model=ApiResponse[GamerProfileRead],
    status_code=status.HTTP_200_OK,
    summary="Update My Gamer Profile",
    description=(
        "Updates one or more attributes of the authenticated user's gamer profile. "
        "Supports partial updates—omitted fields remain unchanged."
    ),
    responses={
        200: {"description": "Gamer profile updated successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Gamer profile not found"},
        422: {"description": "Input validation error"},
    },
)
async def update_my_profile(
    current_user: CurrentUser,
    profile_service: ProfileServiceDep,
    payload: GamerProfileUpdate = Body(
        ...,
        openapi_examples={
            "partial_update": {
                "summary": "Partial Profile Update",
                "value": {
                    "display_name": "ShadowStrike_X",
                    "bio": "Now focusing full-time on Premier Division season playoffs.",
                    "preferred_roles": ["Initiator", "Flex"],
                    "availability": "Daily 7PM - 11PM EST",
                },
            }
        },
    ),
) -> ApiResponse[GamerProfileRead]:
    """Update profile details for the currently authenticated user."""
    profile = await profile_service.update_profile(
        user_id=current_user.id,
        update_in=payload,
    )
    return ApiResponse.ok(
        data=GamerProfileRead.model_validate(profile),
        message="Gamer profile updated successfully.",
    )
