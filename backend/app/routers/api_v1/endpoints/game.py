"""
Game Integration Framework API Endpoints.
Provides RESTful interfaces for linking, verifying, synchronizing, and managing external game accounts.
"""

from typing import Any
import uuid

from fastapi import APIRouter, Body, HTTPException, Query, status

from app.core.dependencies import CurrentUser, GameServiceDep
from app.schemas.common import ApiResponse
from app.schemas.game_account import (
    GameAccountLinkRequest,
    GameAccountRead,
    GameAccountSyncResponse,
    GameAccountUpdateRequest,
    PlayerStatRead,
)

router = APIRouter()


@router.post(
    "/accounts",
    response_model=ApiResponse[GameAccountRead],
    status_code=status.HTTP_201_CREATED,
    summary="Link External Game Account",
    description=(
        "Link a third-party gaming platform account (e.g., Riot Games, Steam, Epic Games, Battle.net) "
        "to the authenticated user's profile. If a platform adapter is registered, automatic identity "
        "verification is triggered."
    ),
)
async def link_game_account(
    current_user: CurrentUser,
    game_service: GameServiceDep,
    payload: GameAccountLinkRequest = Body(
        ...,
        examples=[
            {
                "platform": "riot",
                "game_name": "Valorant",
                "account_identifier": "puuid-val-88234-riot",
                "in_game_name": "Valkyrie",
                "tagline": "NA1",
                "region": "na",
                "is_primary": True,
            }
        ],
    ),
) -> ApiResponse[GameAccountRead]:
    account = await game_service.link_account(user_id=current_user.id, payload=payload)
    return ApiResponse.ok(
        data=GameAccountRead.model_validate(account),
        message=f"{account.game_name} account linked successfully",
    )


@router.get(
    "/accounts",
    response_model=ApiResponse[list[GameAccountRead]],
    summary="List Linked Game Accounts",
    description="Retrieve all external gaming platform accounts linked to the authenticated user.",
)
async def get_my_game_accounts(
    current_user: CurrentUser,
    game_service: GameServiceDep,
    game_name: str | None = Query(None, description="Filter accounts by specific game title"),
) -> ApiResponse[list[GameAccountRead]]:
    accounts = await game_service.get_user_accounts(user_id=current_user.id, game_name=game_name)
    data = [GameAccountRead.model_validate(acc) for acc in accounts]
    return ApiResponse.ok(
        data=data,
        message=f"Retrieved {len(data)} linked game account(s)",
    )


@router.get(
    "/accounts/{account_id}",
    response_model=ApiResponse[GameAccountRead],
    summary="Get Game Account Details",
    description="Retrieve metadata, verification status, and raw telemetry for a specific linked game account.",
)
async def get_game_account(
    account_id: uuid.UUID,
    current_user: CurrentUser,
    game_service: GameServiceDep,
) -> ApiResponse[GameAccountRead]:
    account = await game_service.get_account_by_id(user_id=current_user.id, account_id=account_id)
    return ApiResponse.ok(
        data=GameAccountRead.model_validate(account),
        message="Game account details retrieved successfully",
    )


@router.post(
    "/accounts/{account_id}/verify",
    response_model=ApiResponse[GameAccountRead],
    summary="Verify External Account",
    description="Trigger on-demand ownership and identity verification using the registered platform adapter.",
)
async def verify_game_account(
    account_id: uuid.UUID,
    current_user: CurrentUser,
    game_service: GameServiceDep,
    auth_payload: dict[str, Any] | None = Body(None),
) -> ApiResponse[GameAccountRead]:
    account = await game_service.verify_account(
        user_id=current_user.id,
        account_id=account_id,
        auth_payload=auth_payload,
    )
    return ApiResponse.ok(
        data=GameAccountRead.model_validate(account),
        message="Game account verified successfully",
    )


@router.post(
    "/accounts/{account_id}/sync",
    response_model=ApiResponse[GameAccountSyncResponse],
    summary="Synchronize Profile & Stats via Adapter",
    description=(
        "Executes a synchronization cycle via the external platform adapter. Fetches the latest "
        "profile metadata and competitive stats, persisting them to the database."
    ),
)
async def sync_game_account(
    account_id: uuid.UUID,
    current_user: CurrentUser,
    game_service: GameServiceDep,
) -> ApiResponse[GameAccountSyncResponse]:
    account, stats, sync_result = await game_service.sync_account(
        user_id=current_user.id,
        account_id=account_id,
    )

    latest_stat = stats[0] if stats else None
    response_data = GameAccountSyncResponse(
        account_id=account.id,
        platform=account.platform,
        in_game_name=account.in_game_name,
        tagline=account.tagline,
        full_handle=account.full_handle,
        is_verified=account.is_verified,
        synced_at=sync_result.synced_at,
        stats_synced_count=len(stats),
        latest_rank=latest_stat.rank if latest_stat else None,
        latest_win_rate=latest_stat.win_rate if latest_stat else None,
        sync_message=f"Synchronized {len(stats)} competitive record(s) successfully",
    )

    return ApiResponse.ok(
        data=response_data,
        message="Game account synchronization completed successfully",
    )


@router.get(
    "/accounts/{account_id}/stats",
    response_model=ApiResponse[list[PlayerStatRead]],
    summary="Get Account Competitive Stats",
    description="Retrieve all synchronized competitive metrics and historical telemetry for a game account.",
)
async def get_game_account_stats(
    account_id: uuid.UUID,
    current_user: CurrentUser,
    game_service: GameServiceDep,
) -> ApiResponse[list[PlayerStatRead]]:
    stats = await game_service.get_account_stats(
        user_id=current_user.id,
        account_id=account_id,
    )
    data = [PlayerStatRead.model_validate(s) for s in stats]
    return ApiResponse.ok(
        data=data,
        message=f"Retrieved {len(data)} competitive telemetry record(s)",
    )


@router.put(
    "/accounts/{account_id}",
    response_model=ApiResponse[GameAccountRead],
    summary="Update Linked Account Metadata",
    description="Update user-editable fields for a linked game account.",
)
async def update_game_account(
    account_id: uuid.UUID,
    current_user: CurrentUser,
    game_service: GameServiceDep,
    payload: GameAccountUpdateRequest = Body(...),
) -> ApiResponse[GameAccountRead]:
    account = await game_service.update_account(
        user_id=current_user.id,
        account_id=account_id,
        payload=payload,
    )
    return ApiResponse.ok(
        data=GameAccountRead.model_validate(account),
        message="Game account updated successfully",
    )


@router.put(
    "/accounts/{account_id}/primary",
    response_model=ApiResponse[GameAccountRead],
    summary="Set Account As Primary",
    description="Designate this account as the primary account for its game title.",
)
async def set_primary_game_account(
    account_id: uuid.UUID,
    current_user: CurrentUser,
    game_service: GameServiceDep,
) -> ApiResponse[GameAccountRead]:
    account = await game_service.set_primary_account(
        user_id=current_user.id,
        account_id=account_id,
    )
    return ApiResponse.ok(
        data=GameAccountRead.model_validate(account),
        message=f"Account '{account.full_handle}' set as primary for {account.game_name}",
    )


@router.delete(
    "/accounts/{account_id}",
    response_model=ApiResponse[dict[str, bool]],
    summary="Unlink Game Account",
    description="Unlink and remove an external game account, cascading deletion of associated stats.",
)
async def unlink_game_account(
    account_id: uuid.UUID,
    current_user: CurrentUser,
    game_service: GameServiceDep,
) -> ApiResponse[dict[str, bool]]:
    await game_service.unlink_account(user_id=current_user.id, account_id=account_id)
    return ApiResponse.ok(
        data={"unlinked": True},
        message="Game account unlinked successfully",
    )
