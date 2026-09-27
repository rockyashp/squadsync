"""
Gaming News and Esports Pydantic v2 schemas.
"""

from datetime import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field


class NewsArticleCreate(BaseModel):
    """Payload to create or ingest a gaming news article."""
    title: str = Field(..., max_length=255)
    summary: str = Field(...)
    content: str | None = None
    source_url: str | None = None
    image_url: str | None = None
    game: str = Field(default="General", max_length=50)
    category: str = Field(default="Esports", max_length=50)


class NewsArticleResponse(BaseModel):
    """News article representation."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    summary: str
    content: str | None = None
    source_url: str | None = None
    image_url: str | None = None
    game: str
    category: str
    published_at: datetime
