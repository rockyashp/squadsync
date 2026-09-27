"""
Riot Games and Riot Sign-On (RSO) API Endpoints.
Provides RESTful endpoints for:
- Riot Sign-On (RSO) OAuth2 redirect authorization URL generation
- RSO OAuth2 code callback exchange and player account ownership verification
- Valorant competitive telemetry synchronization (PUUID, Summoner Name, Rank, Current Season, Preferred Agent, Competitive Tier)
- Cached Riot profile and telemetry retrieval
"""

import logging
from typing import Any
import uuid

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.core.dependencies import CurrentUser, RiotServiceDep
from app.schemas.common import ApiResponse
from app.schemas.riot import (
    RiotLoginUrlResponse,
    RiotSyncResponse,
)

logger = logging.getLogger("squadsync.routers.riot")

router = APIRouter()


@router.get(
    "/riot/login",
    response_model=ApiResponse[RiotLoginUrlResponse],
    summary="Get Riot Sign-On (RSO) Login URL",
    description=(
        "Generates a Riot Sign-On (RSO) OAuth2 authorization URL. Redirect your client/browser to this URL "
        "to allow the player to authenticate via official Riot Games credentials."
    ),
)
async def get_rso_login_url(
    riot_service: RiotServiceDep,
    state: str | None = Query(
        None,
        description="Optional CSRF state parameter passed through the OAuth2 redirect flow",
    ),
) -> ApiResponse[RiotLoginUrlResponse]:
    url_data = riot_service.get_rso_login_url(state=state)
    return ApiResponse.ok(
        data=url_data,
        message="Riot Sign-On authorization URL generated successfully",
    )


@router.get(
    "/riot/callback",
    response_model=ApiResponse[dict[str, Any]],
    summary="RSO OAuth2 Callback & Token Verification",
    description=(
        "Processes the callback redirect from Riot Sign-On. Exchanges the authorization code for tokens, "
        "retrieves the player's PUUID from the /userinfo endpoint, and links the verified account to the authenticated user."
    ),
)
async def rso_callback(
    code: str = Query(..., description="RSO authorization code returned in callback redirect"),
    current_user: CurrentUser = None,  # type: ignore
    riot_service: RiotServiceDep = None,  # type: ignore
    state: str | None = Query(None, description="Optional OAuth2 state returned by provider"),
) -> ApiResponse[dict[str, Any]]:
    linked_account = await riot_service.handle_rso_callback(
        user_id=current_user.id,
        code=code,
        state=state,
    )

    return ApiResponse.ok(
        data={
            "account_id": str(linked_account.id),
            "puuid": linked_account.account_identifier,
            "summoner_name": linked_account.in_game_name,
            "tagline": linked_account.tagline,
            "is_verified": linked_account.is_verified,
            "game_name": linked_account.game_name,
            "platform": linked_account.platform,
        },
        message="Riot account ownership verified and linked successfully via RSO",
    )


@router.post(
    "/riot/sync",
    response_model=ApiResponse[RiotSyncResponse],
    summary="Synchronize Riot Games Telemetry",
    description=(
        "Synchronizes Valorant competitive telemetry via the Riot Provider Adapter. "
        "Retrieves and normalizes: PUUID, Summoner Name, Rank, Current Season, Preferred Agent, and Competitive Tier. "
        "Stores the raw publisher API payload inside PostgreSQL JSONB."
    ),
)
async def sync_riot(
    current_user: CurrentUser,
    riot_service: RiotServiceDep,
    account_id: uuid.UUID | None = Query(None, description="Optional target GameAccount UUID"),
    puuid: str | None = Query(None, description="Optional Riot PUUID identifier"),
) -> ApiResponse[RiotSyncResponse]:
    sync_result = await riot_service.sync_riot_account(
        user_id=current_user.id,
        account_id=account_id,
        puuid=puuid,
    )

    return ApiResponse.ok(
        data=sync_result,
        message="Riot Games competitive telemetry synchronized successfully",
    )


@router.get(
    "/riot/me",
    response_model=ApiResponse[RiotSyncResponse],
    summary="Get Current User's Riot Profile",
    description=(
        "Retrieve cached Valorant competitive telemetry for the authenticated user: "
        "PUUID, Summoner Name, Rank, Current Season, Preferred Agent, and Competitive Tier."
    ),
)
async def get_my_riot_profile(
    current_user: CurrentUser,
    riot_service: RiotServiceDep,
) -> ApiResponse[RiotSyncResponse]:
    profile_data = await riot_service.get_riot_profile(user_id=current_user.id)
    return ApiResponse.ok(
        data=profile_data,
        message="Riot competitive profile retrieved successfully",
    )
