"""
GamerProfile SQLAlchemy 2.0 ORM model.
Stores gamer persona, display name, bio, region, language, preferred games, roles, availability, and avatar.
"""

from typing import TYPE_CHECKING
import uuid

from sqlalchemy import ForeignKey, Index, String, Text, Uuid
from sqlalchemy import JSON as JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class GamerProfile(Base, TimestampMixin):
    """
    GamerProfile entity storing user preferences, display name, bio, preferred games/roles, and schedule.
    1-to-1 relationship with User.
    """

    __tablename__ = "gamer_profiles"

    # UUID Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False,
    )

    # Foreign Key to User (Cascade Delete on DB and ORM level)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    # Primary Profile Attributes
    display_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="In-game display name / moniker",
    )
    bio: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Player biography and playstyle summary",
    )
    region: Mapped[str | None] = mapped_column(
        String(50),
        index=True,
        nullable=True,
        comment="Server region, e.g. 'NA-East', 'EU-West'",
    )
    language: Mapped[str | None] = mapped_column(
        String(20),
        default="en",
        nullable=True,
        comment="Primary communication language",
    )
    preferred_games: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
        comment="List of preferred game titles",
    )
    preferred_roles: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
        comment="List of preferred team roles",
    )
    availability: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Weekly gaming schedule / availability window",
    )
    avatar: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="Public URL pointing to profile avatar",
    )

    # Legacy attributes preserved for backwards-compatibility
    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    favorite_game: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    rank: Mapped[str | None] = mapped_column(String(50), nullable=True)
    preferred_role: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    gaming_schedule: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    @property
    def gamer_tag(self) -> str | None:
        return self.display_name or self.full_name

    # JSONB for extended preferences (voice comms, crossplay, playstyle tags)
    preferences: Mapped[dict | None] = mapped_column(
        JSONB,
        default=dict,
        nullable=True,
    )

    # Relationship back to User
    user: Mapped["User"] = relationship(
        "User",
        back_populates="profile",
    )

    __table_args__ = (
        Index("ix_gamer_profiles_region_created", "region", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<GamerProfile id={self.id} user_id={self.user_id} display_name={self.display_name or self.full_name}>"
