"""
User service handling user business logic, state management, and lifecycle.
Delegates database queries to UserRepository conforming to the Repository Pattern (SOLID - SRP & DIP).
"""

from typing import Any
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.base import BaseService


class UserService(BaseService[User]):
    """
    Domain service encapsulating business rules and state management for User accounts.
    """

    def __init__(
        self,
        db: AsyncSession,
        user_repo: UserRepository | None = None,
    ) -> None:
        super().__init__(db)
        self.user_repo = user_repo or UserRepository(db)

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Retrieve a user by their UUID primary key."""
        return await self.user_repo.get_by_id(user_id)

    async def get_by_email(self, email: str) -> User | None:
        """Retrieve a user by their email address (case-insensitive)."""
        return await self.user_repo.get_by_email(email)

    async def get_by_username(self, username: str) -> User | None:
        """Retrieve a user by their username (case-insensitive)."""
        return await self.user_repo.get_by_username(username)

    async def get_by_username_or_email(self, identifier: str) -> User | None:
        """Retrieve a user by either username or email address."""
        return await self.user_repo.get_by_username_or_email(identifier)

    async def create_user(self, username: str, email: str, password_hash: str) -> User:
        """Persist a new User with initial active state."""
        return await self.user_repo.create_user(
            username=username,
            email=email,
            password_hash=password_hash,
        )

    async def record_failed_attempt(self, user: User, max_attempts: int = 5) -> int:
        """
        Increment failed login attempt counter.
        Locks the account if threshold is reached.
        """
        return await self.user_repo.record_failed_attempt(user, max_attempts=max_attempts)

    async def reset_failed_attempts(self, user: User) -> None:
        """Reset failed login attempt counter to 0 upon successful login."""
        await self.user_repo.reset_failed_attempts(user)
