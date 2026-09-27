"""
Team and TeamMember SQLAlchemy 2.0 ORM models.
Represents persistent squads, membership rosters, and tactical roles.
"""

from typing import TYPE_CHECKING
import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Team(Base, TimestampMixin):
    """
    Team entity representing competitive gaming squads.
    """

    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    game: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    synergy_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    max_members: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False,
    )

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], lazy="joined")
    members: Mapped[list["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="team",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Team id={self.id} name={self.name} game={self.game}>"


class TeamMember(Base, TimestampMixin):
    """
    Association table binding users to squads with an assigned tactical role.
    """

    __tablename__ = "team_members"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False,
    )

    team_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(50),
        default="Flex",
        nullable=False,
    )

    # Relationships
    team: Mapped["Team"] = relationship("Team", back_populates="members")
    user = relationship("User", foreign_keys=[user_id], lazy="joined")

    __table_args__ = (
        UniqueConstraint("team_id", "user_id", name="uq_team_members_team_user"),
    )

    def __repr__(self) -> str:
        return f"<TeamMember team={self.team_id} user={self.user_id} role={self.role}>"
