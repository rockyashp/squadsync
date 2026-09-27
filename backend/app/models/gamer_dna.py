"""
GamerDNA SQLAlchemy 2.0 ORM model.
Stores psychometric trait ratings, role affinities, personality archetypes, and raw evaluation JSON.
"""

from typing import TYPE_CHECKING
import uuid

from sqlalchemy import ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy import JSON as JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class GamerDNA(Base, TimestampMixin):
    """
    GamerDNA entity representing behavioral psychometrics, trait ratings, and role classifications.
    1-to-1 relationship with User. Stores full affinity vectors and radar chart geometry in raw_evaluation JSONB.
    """

    __tablename__ = "gamer_dna"

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

    # Psychometric Trait Scores (0 to 100 scale)
    leadership: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Leadership dimension score (0-100)",
    )
    communication: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Communication dimension score (0-100)",
    )
    teamwork: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Teamwork dimension score (0-100)",
    )
    strategy: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Strategy dimension score (0-100)",
    )
    aggression: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Aggression dimension score (0-100)",
    )
    confidence: Mapped[int] = mapped_column(
        Integer,
        default=50,
        nullable=False,
        comment="Confidence dimension score (0-100)",
    )

    # Role & Archetype Classification
    primary_role: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
        comment="Primary gamer archetype (Leader, Support, Strategist, Duelist, Sentinel, Controller)",
    )
    secondary_role: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Secondary supportive archetype",
    )
    personality: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
        comment="Personality archetype moniker, e.g. 'Tactical In-Game Leader'",
    )
    reasoning: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Algorithmic rationale explaining the classification",
    )

    # Raw evaluation data: radar coordinates, role affinity scores, strengths/weaknesses
    raw_evaluation: Mapped[dict | None] = mapped_column(
        JSONB,
        default=dict,
        nullable=True,
        comment="Comprehensive classification breakdown, affinity vector, radar chart coordinates",
    )

    # Relationship back to User
    user: Mapped["User"] = relationship(
        "User",
        back_populates="gamer_dna",
    )

    __table_args__ = (
        Index("ix_gamer_dna_role_confidence", "primary_role", "confidence"),
    )

    def __repr__(self) -> str:
        return (
            f"<GamerDNA id={self.id} user_id={self.user_id} "
            f"primary_role={self.primary_role} personality={self.personality}>"
        )
