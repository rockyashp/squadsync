"""
Team and Squad Management API endpoints.
Provides squad creation from AI recommendations, roster management, and BR-3 isolation.
"""

import uuid
from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser, DatabaseSession
from app.schemas.common import ApiResponse
from app.schemas.team import TeamCreate, TeamInviteRequest, TeamResponse
from app.services.team_service import TeamService

router = APIRouter()


@router.post(
    "",
    response_model=ApiResponse[TeamResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Persistent Squad",
    description="Creates a squad from AI recommendations or custom formation with initial members.",
)
async def create_squad(
    payload: TeamCreate,
    current_user: CurrentUser,
    db: DatabaseSession,
):
    service = TeamService(db)
    team = await service.create_team(owner=current_user, payload=payload)
    return ApiResponse.ok(data=team, message="Squad created successfully.")


@router.get(
    "/my",
    response_model=ApiResponse[list[TeamResponse]],
    summary="Get My Squads",
    description="Lists all competitive squads the authenticated gamer belongs to.",
)
async def get_my_squads(
    current_user: CurrentUser,
    db: DatabaseSession,
):
    service = TeamService(db)
    teams = await service.get_my_teams(current_user.id)
    return ApiResponse.ok(data=teams, message="Squads retrieved successfully.")


@router.get(
    "/{team_id}",
    response_model=ApiResponse[TeamResponse],
    summary="Get Squad Details",
    description="Fetches squad roster and synergy score. Enforces BR-3 (squad dashboard restricted to members).",
)
async def get_squad_details(
    team_id: uuid.UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
):
    service = TeamService(db)
    team = await service.get_team(team_id=team_id, current_user_id=current_user.id)
    return ApiResponse.ok(data=team, message="Squad details retrieved successfully.")


@router.post(
    "/{team_id}/invite",
    response_model=ApiResponse[TeamResponse],
    summary="Invite Member to Squad",
    description="Adds a gamer into the squad roster with a defined tactical role (max 5 players).",
)
async def invite_member(
    team_id: uuid.UUID,
    payload: TeamInviteRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
):
    service = TeamService(db)
    team = await service.add_member(team_id=team_id, current_user_id=current_user.id, invite=payload)
    return ApiResponse.ok(data=team, message="Player added to squad roster.")


@router.delete(
    "/{team_id}/members/{user_id}",
    response_model=ApiResponse[bool],
    summary="Remove Member from Squad",
    description="Removes a member from squad roster. Allowed by squad leader or member leaving.",
)
async def remove_member(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
):
    service = TeamService(db)
    await service.remove_member(team_id=team_id, current_user_id=current_user.id, target_user_id=user_id)
    return ApiResponse.ok(data=True, message="Member removed from squad.")
