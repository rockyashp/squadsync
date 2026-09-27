"""
Admin Dashboard, User Moderation & Platform Analytics schemas.
"""

from datetime import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field


class UserStatusUpdate(BaseModel):
    """Payload to moderate user account status."""
    is_active: bool | None = None
    is_locked: bool | None = None


class UserReportCreate(BaseModel):
    """Payload to file a moderation report against a user."""
    reported_user_id: uuid.UUID = Field(..., description="ID of the user being reported")
    reason: str = Field(..., min_length=3, max_length=100, description="Category/reason for report")
    details: str | None = Field(None, max_length=1000, description="Elaborated details")


class UserReportResponse(BaseModel):
    """User report details representation."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reporter_id: uuid.UUID
    reporter_username: str | None = None
    reported_user_id: uuid.UUID
    reported_username: str | None = None
    reason: str
    details: str | None = None
    status: str
    created_at: datetime


class ReportStatusUpdate(BaseModel):
    """Payload to update report status (BR-6)."""
    status: str = Field(..., pattern="^(PENDING|REVIEWED|RESOLVED|DISMISSED)$")


class PlatformAnalytics(BaseModel):
    """High-level platform KPI metrics for Admin Dashboard."""
    total_users: int
    active_users: int
    total_squads: int
    total_surveys_completed: int
    total_friendships: int
    pending_reports: int
