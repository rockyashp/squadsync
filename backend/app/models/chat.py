"""
ChatMessage SQLAlchemy 2.0 ORM model.
Represents one-to-one and team chat communication records.
"""

from typing import TYPE_CHECKING
import uuid

from sqlalchemy import Boolean, ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.team import Team
    from app.models.user import User


class ChatMessage(Base, TimestampMixin):
    """
    ChatMessage entity storing real-time and historical chat logs.
    Supports both direct 1-to-1 messages (when recipient_id is set)
    and team squad channels (when team_id is set).
    """

    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False,
    )

    sender_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    recipient_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    team_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], lazy="joined")
    recipient = relationship("User", foreign_keys=[recipient_id], lazy="joined")
    team = relationship("Team", foreign_keys=[team_id], lazy="joined")

    def __repr__(self) -> str:
        return f"<ChatMessage id={self.id} sender={self.sender_id} team={self.team_id}>"
