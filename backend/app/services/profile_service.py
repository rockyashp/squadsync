"""
GamerProfile service handling business rules, validation, and delegating data access to ProfileRepository.
"""

from typing import Any
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gamer_profile import GamerProfile
from app.repositories.profile_repository import ProfileRepository
from app.schemas.profile import GamerProfileCreate, GamerProfileUpdate
from app.services.base import BaseService


class ProfileService(BaseService[GamerProfile]):
    """Encapsulates all business logic and orchestration for GamerProfile entities."""

    def __init__(
        self,
        db: AsyncSession,
        profile_repo: ProfileRepository | None = None,
        repo: ProfileRepository | None = None,
    ) -> None:
        super().__init__(db)
        self.repo = profile_repo or repo or ProfileRepository(db)
        self.profile_repo = self.repo

    async def get_by_user_id(self, user_id: uuid.UUID) -> GamerProfile | None:
        """Fetch a gamer profile by associated user ID."""
        return await self.repo.get_by_user_id(user_id)

    async def get_by_user_id_or_404(self, user_id: uuid.UUID) -> GamerProfile:
        """Fetch a gamer profile or raise 404 Not Found."""
        profile = await self.get_by_user_id(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gamer profile not found. Please create a profile first.",
            )
        return profile

    async def create_profile(
        self,
        user_id: uuid.UUID,
        profile_in: GamerProfileCreate,
    ) -> GamerProfile:
        """
        Creates a gamer profile for the specified user.
        Raises 409 Conflict if a profile already exists for the user.
        """
        existing = await self.get_by_user_id(user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A gamer profile already exists for this account.",
            )

        data = profile_in.model_dump(exclude_unset=True)

        profile = GamerProfile(
            user_id=user_id,
            display_name=data.get("display_name") or data.get("full_name"),
            bio=data.get("bio"),
            region=data.get("region"),
            language=data.get("language", "en"),
            preferred_games=data.get("preferred_games") or ([data["favorite_game"]] if data.get("favorite_game") else []),
            preferred_roles=data.get("preferred_roles") or ([data["preferred_role"]] if data.get("preferred_role") else []),
            availability=data.get("availability") or data.get("gaming_schedule"),
            avatar=data.get("avatar") or data.get("avatar_url"),
            # Legacy fallbacks
            full_name=data.get("full_name") or data.get("display_name"),
            favorite_game=data.get("favorite_game") or (data["preferred_games"][0] if data.get("preferred_games") else None),
            rank=data.get("rank"),
            preferred_role=data.get("preferred_role") or (data["preferred_roles"][0] if data.get("preferred_roles") else None),
            gaming_schedule=data.get("gaming_schedule") or data.get("availability"),
            avatar_url=data.get("avatar_url") or data.get("avatar"),
        )

        return await self.repo.save_profile(profile)

    async def update_profile(
        self,
        user_id: uuid.UUID,
        update_in: GamerProfileUpdate,
    ) -> GamerProfile:
        """
        Updates an existing gamer profile with partial attributes.
        Raises 404 Not Found if no profile exists.
        """
        profile = await self.get_by_user_id_or_404(user_id)
        update_data = update_in.model_dump(exclude_unset=True)

        # Synchronize field mappings
        if "display_name" in update_data and not update_data.get("full_name"):
            update_data["full_name"] = update_data["display_name"]
        elif "full_name" in update_data and not update_data.get("display_name"):
            update_data["display_name"] = update_data["full_name"]

        if "avatar" in update_data and not update_data.get("avatar_url"):
            update_data["avatar_url"] = update_data["avatar"]
        elif "avatar_url" in update_data and not update_data.get("avatar"):
            update_data["avatar"] = update_data["avatar_url"]

        if "availability" in update_data and not update_data.get("gaming_schedule"):
            update_data["gaming_schedule"] = update_data["availability"]
        elif "gaming_schedule" in update_data and not update_data.get("availability"):
            update_data["availability"] = update_data["gaming_schedule"]

        return await self.repo.update_profile(profile, update_data)

    async def delete_profile(self, user_id: uuid.UUID) -> None:
        """Deletes a gamer profile for the given user."""
        profile = await self.get_by_user_id_or_404(user_id)
        await self.repo.delete_profile(profile)
