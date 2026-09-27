"""
User SQLAlchemy 2.0 ORM model.
Represents gamer accounts, authentication credentials, and account security states.
"""

from typing import TYPE_CHECKING
import uuid

from sqlalchemy import Boolean, Integer, String, Uuid
from sqlalchemy import JSON as JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.game_account import GameAccount
    from app.models.gamer_dna import GamerDNA
    from app.models.gamer_profile import GamerProfile
    from app.models.player_stat import PlayerStat
    from app.models.survey_answer import SurveyAnswer


class User(Base, TimestampMixin):
    """
    User entity representing system accounts with authentication, security state,
    and cascading relationships to profiles, linked game accounts, stats, and DNA evaluations.
    """

    __tablename__ = "users"

    # UUID Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False,
    )

    # Authentication & Identity
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Account State & Security Controls
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    is_locked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # JSONB for security telemetry, device info, and audit context
    raw_metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        default=dict,
        nullable=True,
    )

    # Relationships (Cascade Delete on ORM and DB level)
    profile: Mapped["GamerProfile | None"] = relationship(
        "GamerProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    game_accounts: Mapped[list["GameAccount"]] = relationship(
        "GameAccount",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    player_stats: Mapped[list["PlayerStat"]] = relationship(
        "PlayerStat",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    survey_answers: Mapped[list["SurveyAnswer"]] = relationship(
        "SurveyAnswer",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # Backwards compatibility alias for survey responses
    @property
    def survey_responses(self) -> list["SurveyAnswer"]:
        return self.survey_answers

    gamer_dna: Mapped["GamerDNA | None"] = relationship(
        "GamerDNA",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username} email={self.email}>"
