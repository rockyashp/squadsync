"""
SurveyAnswer SQLAlchemy 2.0 ORM model.
Stores granular responses to behavioral Gamer DNA questions with telemetry metadata.
"""

from typing import TYPE_CHECKING
import uuid

from sqlalchemy import ForeignKey, Index, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy import JSON as JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class SurveyAnswer(Base, TimestampMixin):
    """
    SurveyAnswer entity storing individual user responses to psychometric questions.
    Ensures exactly one answer per question per user via composite UniqueConstraint.
    Supports JSONB metadata for response duration, input latency, and context.
    """

    __tablename__ = "survey_answers"

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
        index=True,
        nullable=False,
    )

    # Question & Answer Attributes
    question_id: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
        comment="Survey question identifier, e.g., 'lead_01'",
    )
    category: Mapped[str | None] = mapped_column(
        String(50),
        index=True,
        nullable=True,
        comment="Behavioral dimension: Leadership, Communication, Teamwork, Strategy, Aggression",
    )
    selected_option_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Chosen option identifier, e.g., 'lead_01_a'",
    )
    answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Text representation of chosen response",
    )
    score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Numerical score allocated to this choice",
    )

    # JSONB for client response telemetry (dwell time, question sequence, client device)
    raw_metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        default=dict,
        nullable=True,
    )

    # Relationship back to User
    user: Mapped["User"] = relationship(
        "User",
        back_populates="survey_answers",
    )

    # Constraints & Composite Indexes
    __table_args__ = (
        UniqueConstraint(
            "user_id", "question_id",
            name="uq_survey_answers_user_question",
        ),
        Index("ix_survey_answers_user_question", "user_id", "question_id"),
        Index("ix_survey_answers_category_score", "category", "score"),
    )

    def __repr__(self) -> str:
        return f"<SurveyAnswer id={self.id} user_id={self.user_id} question_id={self.question_id} score={self.score}>"


# Backwards compatibility alias
SurveyResponse = SurveyAnswer
