"""
UserRepository implementation.
Decouples database access and query mechanics for User entities from the domain layer.
Conforms to SQLAlchemy 2.0 and the Repository Pattern (SOLID - SRP & DIP).
"""

from collections.abc import Sequence
from datetime import datetime, timezone
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository handling database interactions for User records.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        """Retrieve a user by their email address (case-insensitive)."""
        stmt = select(User).where(func.lower(User.email) == email.lower().strip())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """Retrieve a user by their username (case-insensitive)."""
        stmt = select(User).where(func.lower(User.username) == username.lower().strip())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username_or_email(self, identifier: str) -> User | None:
        """Retrieve a user by either username or email address."""
        cleaned = identifier.lower().strip()
        stmt = select(User).where(
            or_(
                func.lower(User.username) == cleaned,
                func.lower(User.email) == cleaned,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, username: str, email: str, password_hash: str) -> User:
        """Persist a new User in the database."""
        user = User(
            username=username.strip(),
            email=email.lower().strip(),
            password_hash=password_hash,
            is_active=True,
            failed_login_attempts=0,
            is_locked=False,
        )
        return await self.create(user)

    async def record_failed_attempt(self, user: User, max_attempts: int = 5) -> int:
        """
        Increments failed login counter. If threshold is reached, locks account.
        Returns the updated attempt count.
        """
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= max_attempts:
            user.is_locked = True
        await self.update(user)
        return user.failed_login_attempts

    async def reset_failed_attempts(self, user: User) -> None:
        """Resets failed login counter to zero after successful authentication."""
        user.failed_login_attempts = 0
        await self.update(user)
