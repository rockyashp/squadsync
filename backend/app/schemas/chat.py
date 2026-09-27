"""
Chat & Real-Time Messaging Pydantic v2 schemas.
"""

from datetime import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageCreate(BaseModel):
    """Payload to send a message via REST or validate incoming WebSocket payload."""
    recipient_id: uuid.UUID | None = Field(None, description="Target recipient for 1-to-1 direct message")
    team_id: uuid.UUID | None = Field(None, description="Target squad channel for team message")
    content: str = Field(..., min_length=1, max_length=2000, description="Message text content")


class ChatMessageResponse(BaseModel):
    """Message representation returned in history and WebSocket events."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sender_id: uuid.UUID
    sender_username: str | None = None
    recipient_id: uuid.UUID | None = None
    team_id: uuid.UUID | None = None
    content: str
    is_read: bool = False
    created_at: datetime


class MarkReadRequest(BaseModel):
    """Payload to mark incoming messages as read."""
    sender_id: uuid.UUID | None = None
    team_id: uuid.UUID | None = None
