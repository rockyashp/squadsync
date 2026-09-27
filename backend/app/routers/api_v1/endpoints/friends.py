"""
Friendship & Social Networking API endpoints.
Provides global gamer search, friend requests, friends list, and blocking rules (BR-2).
"""

import uuid
from fastapi import APIRouter, Query, status

from app.core.dependencies import CurrentUser, DatabaseSession
from app.schemas.common import ApiResponse
from app.schemas.friendship import FriendActionRequest, FriendGamerItem, FriendshipResponse, PlayerSearchResult
from app.services.friendship_service import FriendshipService

router = APIRouter()


@router.post(
    "/request/{user_id}",
    response_model=ApiResponse[FriendshipResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Send Friend Request",
    description="Initiates a friend request to target gamer. Enforces BR-2 (no contact if blocked).",
)
async def send_friend_request(
    user_id: uuid.UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
):
    service = FriendshipService(db)
    friendship = await service.send_request(requester_id=current_user.id, addressee_id=user_id)
    return ApiResponse.ok(data=friendship, message="Friend request sent successfully.")


@router.put(
    "/request/{request_id}",
    response_model=ApiResponse[FriendshipResponse],
    summary="Respond to Friend Request",
    description="Accepts, rejects, or blocks a friend invitation.",
)
async def respond_to_friend_request(
    request_id: uuid.UUID,
    payload: FriendActionRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
):
    service = FriendshipService(db)
    result = await service.respond_to_request(
        request_id=request_id,
        current_user_id=current_user.id,
        action=payload.action,
    )
    return ApiResponse.ok(data=result, message=f"Friend request {payload.action.lower()}ed.")


@router.get(
    "",
    response_model=ApiResponse[list[FriendGamerItem]],
    summary="Get Confirmed Friends List",
    description="Returns all active, confirmed friends with role and profile data.",
)
async def get_friends_list(
    current_user: CurrentUser,
    db: DatabaseSession,
):
    service = FriendshipService(db)
    friends = await service.get_friends_list(current_user.id)
    return ApiResponse.ok(data=friends, message="Friends list retrieved successfully.")


@router.get(
    "/requests",
    response_model=ApiResponse[list[FriendGamerItem]],
    summary="Get Pending Invitations",
    description="Retrieves pending friend requests waiting for action.",
)
async def get_pending_requests(
    current_user: CurrentUser,
    db: DatabaseSession,
):
    service = FriendshipService(db)
    requests = await service.get_pending_requests(current_user.id)
    return ApiResponse.ok(data=requests, message="Pending requests retrieved successfully.")


@router.delete(
    "/{friend_user_id}",
    response_model=ApiResponse[bool],
    summary="Remove Friend",
    description="Removes a player from user's friends list.",
)
async def remove_friend(
    friend_user_id: uuid.UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
):
    service = FriendshipService(db)
    await service.remove_friend(current_user.id, friend_user_id)
    return ApiResponse.ok(data=True, message="Friend removed successfully.")


@router.get(
    "/search",
    response_model=ApiResponse[list[PlayerSearchResult]],
    summary="Search Gamers",
    description="Global player discovery by username, email, or gamer tag.",
)
async def search_players(
    current_user: CurrentUser,
    db: DatabaseSession,
    q: str = Query(..., min_length=1, description="Search term for username or gamer tag"),
):
    service = FriendshipService(db)
    players = await service.search_players(current_user.id, q)
    return ApiResponse.ok(data=players, message=f"Found {len(players)} players matching query.")
