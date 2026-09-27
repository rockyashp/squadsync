"""
GameAccountRepository implementation.
Decouples data access and query mechanics for external game accounts from the domain layer.
"""

from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any
import uuid

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game_account import GameAccount
from app.repositories.base import BaseRepository


class GameAccountRepository(BaseRepository[GameAccount]):
    """
    Repository handling database interactions for linked GameAccount records.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(GameAccount, db)

    async def get_by_user_id(self, user_id: uuid.UUID) -> Sequence[GameAccount]:
        """Fetch all linked game accounts for a user."""
        stmt = (
            select(GameAccount)
            .where(GameAccount.user_id == user_id)
            .order_by(GameAccount.is_primary.desc(), GameAccount.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_user_and_game(
        self, user_id: uuid.UUID, game_name: str
    ) -> Sequence[GameAccount]:
        """Fetch all accounts belonging to a user for a specific game."""
        stmt = (
            select(GameAccount)
            .where(
                and_(
                    GameAccount.user_id == user_id,
                    GameAccount.game_name.ilike(game_name.strip()),
                )
            )
            .order_by(GameAccount.is_primary.desc(), GameAccount.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_user_account_by_platform(
        self, user_id: uuid.UUID, platform: str, account_identifier: str
    ) -> GameAccount | None:
        """Find an account linked to a specific user by platform and identifier."""
        stmt = select(GameAccount).where(
            and_(
                GameAccount.user_id == user_id,
                GameAccount.platform.ilike(platform.strip()),
                GameAccount.account_identifier == account_identifier.strip(),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_platform_and_identifier(
        self, platform: str, account_identifier: str
    ) -> GameAccount | None:
        """Find an account globally across all users by platform and external identifier."""
        stmt = select(GameAccount).where(
            and_(
                GameAccount.platform.ilike(platform.strip()),
                GameAccount.account_identifier == account_identifier.strip(),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_primary_account(
        self, user_id: uuid.UUID, game_name: str | None = None
    ) -> GameAccount | None:
        """Get the primary game account for a user, optionally filtered by game."""
        conditions = [GameAccount.user_id == user_id, GameAccount.is_primary.is_(True)]
        if game_name:
            conditions.append(GameAccount.game_name.ilike(game_name.strip()))

        stmt = select(GameAccount).where(and_(*conditions))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def set_primary_account(
        self, user_id: uuid.UUID, account_id: uuid.UUID, game_name: str
    ) -> GameAccount | None:
        """
        Mark a specific account as primary for a given game and demote any existing primary accounts.
        """
        # Demote existing primary accounts for this user and game
        demote_stmt = (
            update(GameAccount)
            .where(
                and_(
                    GameAccount.user_id == user_id,
                    GameAccount.game_name.ilike(game_name.strip()),
                    GameAccount.id != account_id,
                )
            )
            .values(is_primary=False)
        )
        await self.db.execute(demote_stmt)

        # Promote target account
        account = await self.get_by_id(account_id)
        if account and account.user_id == user_id:
            account.is_primary = True
            await self.db.commit()
            await self.db.refresh(account)
            return account
        return None

    async def update_sync_data(
        self,
        account_id: uuid.UUID,
        raw_data: dict[str, Any],
        in_game_name: str | None = None,
        tagline: str | None = None,
        region: str | None = None,
        is_verified: bool = True,
    ) -> GameAccount | None:
        """Update synchronized profile telemetry on an account."""
        account = await self.get_by_id(account_id)
        if not account:
            return None

        account.raw_profile_data = raw_data
        account.last_synced_at = datetime.now(timezone.utc)
        account.is_verified = is_verified

        if in_game_name:
            account.in_game_name = in_game_name
        if tagline is not None:
            account.tagline = tagline
        if region:
            account.region = region

        await self.db.commit()
        await self.db.refresh(account)
        return account
