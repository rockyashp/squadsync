"""
GameAccount SQLAlchemy 2.0 ORM model.
Represents external gaming accounts (Riot Games, Steam, Epic, Battle.net) linked to a user.
"""

from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint, Uuid
from sqlalchemy import JSON as JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.player_stat import PlayerStat
    from app.models.user import User


class GameAccount(Base, TimestampMixin):
    """
    GameAccount entity representing linked third-party gaming accounts and identifiers.
    Stores raw publisher API payloads in a JSONB column.
    """

    __tablename__ = "game_accounts"

    # UUID Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False,
    )

    # Foreign Key to User (Cascade Delete)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Game & Platform Metadata
    game_name: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
        comment="Game title, e.g., 'Valorant', 'CS2', 'League of Legends'",
    )
    platform: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
        comment="Platform or publisher service, e.g., 'riot', 'steam', 'epic'",
    )
    account_identifier: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
        comment="Immutable external account ID, e.g., Riot PUUID, SteamID64",
    )
    in_game_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Gamer tag / Summoner name / Handle",
    )
    tagline: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Tagline / Discriminator, e.g. 'NA1'",
    )
    region: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Verification & Account State
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Raw API response payload from publisher telemetry
    raw_profile_data: Mapped[dict | None] = mapped_column(
        JSONB,
        default=dict,
        nullable=True,
    )

    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="game_accounts",
    )

    player_stats: Mapped[list["PlayerStat"]] = relationship(
        "PlayerStat",
        back_populates="game_account",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # Composite constraints and indexes
    __table_args__ = (
        UniqueConstraint(
            "user_id", "platform", "account_identifier",
            name="uq_game_accounts_user_platform_identifier",
        ),
        Index("ix_game_accounts_platform_identifier", "platform", "account_identifier"),
        Index("ix_game_accounts_user_game", "user_id", "game_name"),
    )

    @property
    def full_handle(self) -> str:
        """Return composite gamer handle (e.g. 'Valkyrie#NA1' or 'TenZ')."""
        if self.tagline:
            return f"{self.in_game_name}#{self.tagline}"
        return self.in_game_name

    def __repr__(self) -> str:
        return (
            f"<GameAccount id={self.id} user_id={self.user_id} "
            f"game={self.game_name} ign={self.full_handle}>"
        )
