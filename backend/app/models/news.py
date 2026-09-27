"""
NewsArticle SQLAlchemy 2.0 ORM model.
Represents esports tournament notices, game patch notes, and gaming announcements.
"""

from datetime import datetime
import uuid

from sqlalchemy import DateTime, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class NewsArticle(Base, TimestampMixin):
    """
    Gaming news, patch notes, and esports article cache entity.
    """

    __tablename__ = "news_articles"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    image_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    game: Mapped[str] = mapped_column(
        String(50),
        default="General",
        nullable=False,
        index=True,
    )

    category: Mapped[str] = mapped_column(
        String(50),
        default="Esports",
        nullable=False,
        index=True,
    )

    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<NewsArticle id={self.id} title={self.title} game={self.game}>"
