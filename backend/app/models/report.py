"""
UserReport SQLAlchemy 2.0 ORM model.
Represents moderation reports, inappropriate behavior flags, and admin review states.
"""

from enum import Enum
import uuid

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ReportStatus(str, Enum):
    PENDING = "PENDING"
    REVIEWED = "REVIEWED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class UserReport(Base, TimestampMixin):
    """
    Moderation entity for player conduct reports (BR-6 48h review rule).
    """

    __tablename__ = "user_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False,
    )

    reporter_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    reported_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    reason: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default=ReportStatus.PENDING.value,
        nullable=False,
        index=True,
    )

    # Relationships
    reporter = relationship("User", foreign_keys=[reporter_id], lazy="joined")
    reported_user = relationship("User", foreign_keys=[reported_user_id], lazy="joined")

    def __repr__(self) -> str:
        return f"<UserReport id={self.id} reason={self.reason} status={self.status}>"
