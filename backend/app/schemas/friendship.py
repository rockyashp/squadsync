"""
Friendship & Social Pydantic v2 validation and response schemas.
"""

from datetime import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field


class FriendRequestCreate(BaseModel):
    """Payload to send a friend invitation."""
    addressee_id: uuid.UUID = Field(..., description="Target user UUID to invite")


class FriendActionRequest(BaseModel):
    """Payload to respond to a friend request."""
    action: str = Field(..., pattern="^(ACCEPT|REJECT|BLOCK)$", description="Action to perform: ACCEPT, REJECT, or BLOCK")


class FriendshipResponse(BaseModel):
    """Standard friendship record response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    requester_id: uuid.UUID
    addressee_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime | None = None


class FriendGamerItem(BaseModel):
    """Detailed gamer info for friends list."""
    friendship_id: uuid.UUID
    user_id: uuid.UUID
    username: str
    gamer_tag: str | None = None
    avatar_url: str | None = None
    primary_role: str | None = None
    rank_tier: str | None = None
    is_online: bool = True
    direction: str = "incoming"  # incoming, outgoing, friend


class PlayerSearchResult(BaseModel):
    """Global player search result."""
    user_id: uuid.UUID
    username: str
    gamer_tag: str | None = None
    avatar_url: str | None = None
    primary_role: str | None = None
    rank_tier: str | None = None
    friendship_status: str | None = None  # None, PENDING_SENT, PENDING_RECEIVED, ACCEPTED, BLOCKED
