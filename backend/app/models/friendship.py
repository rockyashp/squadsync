"""
Friendship SQLAlchemy 2.0 ORM model.
Represents friend connections, invitations, and blocking states between users.
"""

from enum import Enum
import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class FriendshipStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"


class Friendship(Base, TimestampMixin):
    """
    Friendship relationship between two users.
    Enforces uniqueness so duplicate invitations cannot be initiated between the same pair.
    """

    __tablename__ = "friendships"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False,
    )

    requester_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    addressee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default=FriendshipStatus.PENDING.value,
        nullable=False,
        index=True,
    )

    # Relationships
    requester = relationship("User", foreign_keys=[requester_id], lazy="joined")
    addressee = relationship("User", foreign_keys=[addressee_id], lazy="joined")

    __table_args__ = (
        UniqueConstraint("requester_id", "addressee_id", name="uq_friendships_requester_addressee"),
    )

    def __repr__(self) -> str:
        return f"<Friendship requester={self.requester_id} addressee={self.addressee_id} status={self.status}>"
