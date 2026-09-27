"""
Team and Squad Management Pydantic v2 schemas.
"""

from datetime import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field


class TeamCreate(BaseModel):
    """Payload to create a new squad."""
    name: str = Field(..., min_length=2, max_length=100, description="Squad name")
    game: str = Field(..., min_length=2, max_length=50, description="Target game (e.g. VALORANT, CS2)")
    description: str | None = Field(None, max_length=500, description="Squad description or bio")
    synergy_score: float = Field(default=85.0, ge=0.0, le=100.0, description="Predicted team synergy score")
    member_ids: list[uuid.UUID] = Field(default_factory=list, description="Initial squad member user UUIDs")
    member_roles: dict[str, str] = Field(default_factory=dict, description="Map of string(uuid) -> tactical role")


class TeamInviteRequest(BaseModel):
    """Payload to invite a player into an existing team."""
    user_id: uuid.UUID = Field(..., description="Target user UUID to invite")
    role: str = Field(default="Flex", max_length=50, description="Tactical role for the invited member")


class TeamMemberResponse(BaseModel):
    """Member roster item representation."""
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    username: str
    gamer_tag: str | None = None
    avatar_url: str | None = None
    role: str
    joined_at: datetime


class TeamResponse(BaseModel):
    """Squad details representation."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    game: str
    owner_id: uuid.UUID
    owner_username: str | None = None
    description: str | None = None
    synergy_score: float
    max_members: int
    members: list[TeamMemberResponse] = []
    created_at: datetime
