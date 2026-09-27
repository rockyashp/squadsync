"""
PlayerStatRepository implementation.
Decouples data access and query mechanics for player statistics and telemetry.
"""

from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any
import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.player_stat import PlayerStat
from app.repositories.base import BaseRepository


class PlayerStatRepository(BaseRepository[PlayerStat]):
    """
    Repository handling persistence and querying of competitive telemetry and player stats.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(PlayerStat, db)

    async def get_by_account_id(
        self, game_account_id: uuid.UUID
    ) -> Sequence[PlayerStat]:
        """Fetch all statistics recorded for a given game account."""
        stmt = (
            select(PlayerStat)
            .where(PlayerStat.game_account_id == game_account_id)
            .order_by(PlayerStat.updated_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_user_id(
        self, user_id: uuid.UUID
    ) -> Sequence[PlayerStat]:
        """Fetch all stats records for a user across all accounts."""
        stmt = (
            select(PlayerStat)
            .where(PlayerStat.user_id == user_id)
            .order_by(PlayerStat.updated_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_account_season_mode(
        self,
        game_account_id: uuid.UUID,
        season: str,
        game_mode: str,
    ) -> PlayerStat | None:
        """Find a specific player stat record by account, season, and game mode."""
        stmt = select(PlayerStat).where(
            and_(
                PlayerStat.game_account_id == game_account_id,
                PlayerStat.season == season.strip(),
                PlayerStat.game_mode == game_mode.strip(),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_stat(
        self,
        game_account_id: uuid.UUID,
        user_id: uuid.UUID,
        season: str,
        game_mode: str,
        stat_attributes: dict[str, Any],
    ) -> PlayerStat:
        """
        Create or update a player stat record for a specific account, season, and mode.
        """
        existing = await self.get_by_account_season_mode(
            game_account_id=game_account_id,
            season=season,
            game_mode=game_mode,
        )

        now = datetime.now(timezone.utc)
        if existing:
            for key, val in stat_attributes.items():
                if hasattr(existing, key):
                    setattr(existing, key, val)
            if hasattr(existing, "recorded_at"):
                existing.recorded_at = now
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        new_stat = PlayerStat(
            game_account_id=game_account_id,
            user_id=user_id,
            season=season.strip(),
            game_mode=game_mode.strip(),
            recorded_at=now,
            **stat_attributes,
        )
        self.db.add(new_stat)
        await self.db.commit()
        await self.db.refresh(new_stat)
        return new_stat
