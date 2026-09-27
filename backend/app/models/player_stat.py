"""
PlayerStat SQLAlchemy 2.0 ORM model.
Stores competitive telemetry, performance metrics, and raw publisher stats for game accounts.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any
import uuid

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint, Uuid, func
from sqlalchemy import JSON as JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.game_account import GameAccount
    from app.models.user import User


class PlayerStat(Base, TimestampMixin):
    """
    PlayerStat entity storing seasonal and mode-specific performance metrics,
    along with comprehensive raw telemetry payloads inside JSONB columns.
    """

    __tablename__ = "player_stats"

    # UUID Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False,
    )

    # Foreign Keys
    game_account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("game_accounts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Season & Mode Identification
    season: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
        comment="Season/Act/Split identifier, e.g., 'Episode 8: Act 3'",
    )
    game_mode: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
        comment="Queue/mode, e.g., 'competitive', 'premier', 'ranked'",
    )

    # Competitive Rank Metrics
    current_rank: Mapped[str | None] = mapped_column(
        String(50),
        index=True,
        nullable=True,
        comment="Current tier, e.g. 'Diamond 3'",
    )
    peak_rank: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="All-time peak tier, e.g. 'Ascendant 1'",
    )
    rank_rating: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Rank rating / LP / ELO points",
    )

    # Match Performance Metrics
    matches_played: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    wins: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    losses: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    win_rate: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="Win percentage (0.0 to 100.0)",
    )
    kd_ratio: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="Kill/Death ratio",
    )
    kda: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="Kill/Death/Assist ratio",
    )
    headshot_pct: Mapped[float | None] = mapped_column(
        Float,
        default=0.0,
        nullable=True,
        comment="Headshot percentage",
    )
    score_per_round: Mapped[float | None] = mapped_column(
        Float,
        default=0.0,
        nullable=True,
        comment="Average combat score per round",
    )

    # Complete raw match telemetry from game APIs (Tracker Network, Riot, Valve)
    raw_stats: Mapped[dict | None] = mapped_column(
        JSONB,
        default=dict,
        nullable=True,
        comment="Raw publisher telemetry JSON payload including weapon & agent breakdowns",
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    game_account: Mapped["GameAccount"] = relationship(
        "GameAccount",
        back_populates="player_stats",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="player_stats",
    )

    # Constraints & Indexes
    __table_args__ = (
        UniqueConstraint(
            "game_account_id", "season", "game_mode",
            name="uq_player_stats_account_season_mode",
        ),
        Index("ix_player_stats_user_recorded", "user_id", "recorded_at"),
        Index("ix_player_stats_mode_rank", "game_mode", "current_rank"),
    )

    def __init__(self, **kwargs: Any) -> None:
        if "rank" in kwargs and "current_rank" not in kwargs:
            kwargs["current_rank"] = kwargs.pop("rank")
        if "headshot_percentage" in kwargs and "headshot_pct" not in kwargs:
            kwargs["headshot_pct"] = kwargs.pop("headshot_percentage")
        if "raw_stats_data" in kwargs and "raw_stats" not in kwargs:
            kwargs["raw_stats"] = kwargs.pop("raw_stats_data")
        if "damage_per_round" in kwargs and "score_per_round" not in kwargs:
            kwargs["score_per_round"] = kwargs.pop("damage_per_round")
        super().__init__(**kwargs)

    @property
    def rank(self) -> str | None:
        """Alias for current_rank."""
        return self.current_rank

    @rank.setter
    def rank(self, value: str | None) -> None:
        self.current_rank = value

    @property
    def raw_stats_data(self) -> dict | None:
        """Alias for raw_stats."""
        return self.raw_stats

    @raw_stats_data.setter
    def raw_stats_data(self, value: dict | None) -> None:
        self.raw_stats = value

    @property
    def headshot_percentage(self) -> float | None:
        """Alias for headshot_pct."""
        return self.headshot_pct

    @headshot_percentage.setter
    def headshot_percentage(self, value: float | None) -> None:
        self.headshot_pct = value

    @property
    def damage_per_round(self) -> float | None:
        """Alias for score_per_round."""
        return self.score_per_round

    @damage_per_round.setter
    def damage_per_round(self, value: float | None) -> None:
        self.score_per_round = value

    def __repr__(self) -> str:
        return (
            f"<PlayerStat id={self.id} account_id={self.game_account_id} "
            f"season={self.season} mode={self.game_mode} rank={self.current_rank}>"
        )
