"""
Profile Repository handling database queries and persistence for GamerProfile.
Decouples SQLAlchemy operations from ProfileService business logic.
"""

from typing import Any
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gamer_profile import GamerProfile
from app.repositories.base import BaseRepository


class ProfileRepository(BaseRepository[GamerProfile]):
    """Repository handling all database access for GamerProfile entities."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=GamerProfile, db=db)

    async def get_by_user_id(self, user_id: uuid.UUID) -> GamerProfile | None:
        """Fetch a gamer profile by associated user ID."""
        stmt = select(GamerProfile).where(GamerProfile.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def save_profile(self, profile: GamerProfile) -> GamerProfile:
        """Persist a new profile instance."""
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def update_profile(self, profile: GamerProfile, update_dict: dict[str, Any]) -> GamerProfile:
        """Apply partial attribute updates and commit transaction."""
        for field, value in update_dict.items():
            if hasattr(profile, field):
                setattr(profile, field, value)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def delete_profile(self, profile: GamerProfile) -> None:
        """Delete an existing profile."""
        await self.db.delete(profile)
        await self.db.commit()
