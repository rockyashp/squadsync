"""
Steam Authentication and Dota 2 OpenDota Integration API Endpoints.
Provides RESTful endpoints for:
- Steam OpenID 2.0 login URL generation
- Steam OpenID callback and account ownership verification
- Dota 2 competitive telemetry synchronization (real-time and background)
- Cached Dota 2 profile, MMR, medal rank, favorite heroes, and recent matches retrieval
"""

from datetime import datetime, timezone
import logging
from typing import Any
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status

from app.core.dependencies import CurrentUser, Dota2ServiceDep
from app.schemas.common import ApiResponse
from app.schemas.dota2 import (
    Dota2SyncResponse,
    SteamLoginUrlResponse,
)
from app.services.dota2_service import run_background_dota2_sync

logger = logging.getLogger("squadsync.routers.steam_dota")

router = APIRouter()


@router.get(
    "/steam/login",
    response_model=ApiResponse[SteamLoginUrlResponse],
    summary="Get Steam OpenID Login URL",
    description=(
        "Generates a Valve Steam OpenID 2.0 redirect URL. Direct your client/browser to this URL "
        "to allow the user to authenticate on the official Steam Community website."
    ),
)
async def get_steam_login_url(
    dota2_service: Dota2ServiceDep,
    return_to: str | None = Query(
        None,
        description="Optional custom frontend callback URL where Steam redirects with assertion parameters",
    ),
) -> ApiResponse[SteamLoginUrlResponse]:
    url_data = dota2_service.get_steam_login_url(return_to=return_to)
    return ApiResponse.ok(
        data=url_data,
        message="Steam OpenID authentication URL generated successfully",
    )


@router.get(
    "/steam/callback",
    response_model=ApiResponse[dict[str, Any]],
    summary="Steam OpenID Callback & Ownership Verification",
    description=(
        "Processes the callback from Steam OpenID 2.0. Verifies cryptographic signature with Valve's "
        "servers (openid.mode=check_authentication), extracts the 64-bit SteamID, and links the verified "
        "account to the authenticated user."
    ),
)
async def steam_callback(
    request: Request,
    current_user: CurrentUser,
    dota2_service: Dota2ServiceDep,
) -> ApiResponse[dict[str, Any]]:
    # Extract all OpenID parameters from the incoming query string
    openid_params = dict(request.query_params)
    if not openid_params:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing OpenID query parameters from Steam callback",
        )

    linked_account = await dota2_service.verify_and_link_steam(
        user_id=current_user.id,
        openid_params=openid_params,
    )

    return ApiResponse.ok(
        data={
            "account_id": str(linked_account.id),
            "steam_id": linked_account.account_identifier,
            "player_name": linked_account.in_game_name,
            "is_verified": linked_account.is_verified,
            "game_name": linked_account.game_name,
            "platform": linked_account.platform,
        },
        message="Steam account ownership verified and linked successfully",
    )


@router.post(
    "/dota2/sync",
    response_model=ApiResponse[Dota2SyncResponse],
    summary="Synchronize Dota 2 Telemetry",
    description=(
        "Synchronizes Dota 2 competitive telemetry via the OpenDota API. "
        "Retrieves MMR estimate, medal rank, wins, losses, favorite heroes, and recent matches. "
        "Stores the complete raw publisher API responses inside PostgreSQL JSONB. "
        "Set ?background=true to offload telemetry refresh to a background worker task."
    ),
)
async def sync_dota2(
    current_user: CurrentUser,
    dota2_service: Dota2ServiceDep,
    background_tasks: BackgroundTasks,
    account_id: uuid.UUID | None = Query(None, description="Optional target GameAccount UUID"),
    steam_id: str | None = Query(None, description="Optional 64-bit Steam ID (e.g. 76561198000000000)"),
    background: bool = Query(default=False, description="Whether to execute sync in background worker task"),
) -> ApiResponse[Dota2SyncResponse]:
    if background:
        # Resolve target account or default Dota 2 account
        account = await dota2_service.get_or_create_dota_account(
            user_id=current_user.id,
            steam_id=steam_id or "76561198000000000",
        ) if steam_id else None

        if not account and account_id:
            account = await dota2_service.account_repo.get_by_id(account_id)

        target_acc_id = account.id if account else account_id or uuid.uuid4()
        background_tasks.add_task(
            run_background_dota2_sync,
            user_id=current_user.id,
            account_id=target_acc_id,
        )

        # Return fast acknowledgment response
        return ApiResponse.ok(
            data=Dota2SyncResponse(
                account_id=target_acc_id,
                user_id=current_user.id,
                steam_id=account.account_identifier if account else (steam_id or "pending"),
                player_name=account.in_game_name if account else "Syncing...",
                avatar=None,
                mmr=None,
                rank="Syncing in Background...",
                wins=0,
                losses=0,
                favorite_heroes=[],
                recent_matches=[],
                is_verified=account.is_verified if account else False,
                last_synced_at=account.last_synced_at if (account and account.last_synced_at) else datetime.now(timezone.utc),
                sync_mode="background",
            ),
            message="Dota 2 telemetry refresh scheduled in background task",
        )

    # Real-time synchronization
    sync_result = await dota2_service.sync_dota2_account(
        user_id=current_user.id,
        account_id=account_id,
        steam_id=steam_id,
        sync_mode="realtime",
    )

    return ApiResponse.ok(
        data=sync_result,
        message="Dota 2 telemetry synchronized successfully",
    )


@router.get(
    "/dota2/me",
    response_model=ApiResponse[Dota2SyncResponse],
    summary="Get Current User's Dota 2 Profile",
    description="Retrieve cached competitive Dota 2 telemetry, MMR, medal rank, favorite heroes, and recent matches.",
)
async def get_my_dota2_profile(
    current_user: CurrentUser,
    dota2_service: Dota2ServiceDep,
) -> ApiResponse[Dota2SyncResponse]:
    profile_data = await dota2_service.get_dota2_profile(user_id=current_user.id)
    return ApiResponse.ok(
        data=profile_data,
        message="Dota 2 competitive profile retrieved successfully",
    )
