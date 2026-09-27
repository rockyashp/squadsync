"""
GameService domain service implementation.
Coordinates game account lifecycle, provider adapter resolution, synchronization, and telemetry persistence.
"""

from collections.abc import Sequence
from datetime import datetime, timezone
import logging
from typing import Any
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictException,
    EntityNotFoundException,
    ValidationException,
)
from app.models.game_account import GameAccount
from app.models.player_stat import PlayerStat
from app.providers.dto import (
    AccountVerificationResult,
    ProviderProfileData,
    ProviderStatsData,
    ProviderSyncResult,
)
from app.providers.exceptions import (
    AccountVerificationException,
    ProviderException,
    ProviderNotFoundException,
)
from app.providers.registry import GameProviderRegistry, provider_registry as default_registry
from app.repositories.game_account_repository import GameAccountRepository
from app.repositories.player_stat_repository import PlayerStatRepository
from app.schemas.game_account import GameAccountLinkRequest, GameAccountUpdateRequest

logger = logging.getLogger("squadsync.game_service")


class GameService:
    """
    Domain service orchestrating external game account linking, adapter pattern
    telemetry syncing, and competitive statistics persistence.
    """

    def __init__(
        self,
        db: AsyncSession,
        account_repo: GameAccountRepository | None = None,
        stat_repo: PlayerStatRepository | None = None,
        registry: GameProviderRegistry | None = None,
    ) -> None:
        self.db = db
        self.account_repo = account_repo or GameAccountRepository(db)
        self.stat_repo = stat_repo or PlayerStatRepository(db)
        self.registry = registry or default_registry

    async def link_account(
        self,
        user_id: uuid.UUID,
        payload: GameAccountLinkRequest,
    ) -> GameAccount:
        """
        Link an external game account to the user.
        If an adapter is registered for the platform, verifies account before persistence.
        """
        # 1. Check if user already linked this specific external identifier
        existing = await self.account_repo.get_user_account_by_platform(
            user_id=user_id,
            platform=payload.platform,
            account_identifier=payload.account_identifier,
        )
        if existing:
            raise ConflictException(
                f"You have already linked this {payload.platform} account ({payload.account_identifier}) "
                f"for {payload.game_name}."
            )

        is_verified = False
        in_game_name = payload.in_game_name
        tagline = payload.tagline
        region = payload.region
        raw_profile: dict[str, Any] = {}

        # 2. If provider adapter is registered, attempt online verification
        if self.registry.has_provider(payload.platform):
            provider = self.registry.get(payload.platform)
            try:
                verification = await provider.verify_account(
                    account_identifier=payload.account_identifier,
                    auth_payload=payload.auth_payload,
                )
                if verification.is_valid:
                    is_verified = True
                    in_game_name = verification.in_game_name or in_game_name
                    tagline = verification.tagline or tagline
                    region = verification.region or region
                    raw_profile = verification.metadata
                else:
                    logger.warning(
                        f"Account verification failed for {payload.platform}:{payload.account_identifier}: "
                        f"{verification.error_message}"
                    )
            except ProviderException as e:
                logger.error(f"Provider error during verification: {e.message}")
                # We still allow linking with is_verified=False unless strict check is requested

        # 3. Handle primary account demotion if requested
        if payload.is_primary:
            current_primary = await self.account_repo.get_primary_account(
                user_id=user_id, game_name=payload.game_name
            )
            if current_primary:
                current_primary.is_primary = False
                await self.account_repo.update(current_primary)

        # 4. Instantiate and persist GameAccount
        new_account = GameAccount(
            user_id=user_id,
            game_name=payload.game_name,
            platform=payload.platform.lower(),
            account_identifier=payload.account_identifier,
            in_game_name=in_game_name,
            tagline=tagline,
            region=region,
            is_verified=is_verified,
            is_primary=payload.is_primary,
            raw_profile_data=raw_profile,
            last_synced_at=datetime.now(timezone.utc) if is_verified else None,
        )

        return await self.account_repo.create(new_account)

    async def get_user_accounts(
        self,
        user_id: uuid.UUID,
        game_name: str | None = None,
    ) -> Sequence[GameAccount]:
        """Fetch all game accounts linked by the user."""
        if game_name:
            return await self.account_repo.get_by_user_and_game(user_id, game_name)
        return await self.account_repo.get_by_user_id(user_id)

    async def get_account_by_id(
        self,
        user_id: uuid.UUID,
        account_id: uuid.UUID,
    ) -> GameAccount:
        """Fetch a specific game account and ensure user ownership."""
        account = await self.account_repo.get_by_id(account_id)
        if not account or account.user_id != user_id:
            raise EntityNotFoundException(
                f"Game account with ID '{account_id}' was not found for this user."
            )
        return account

    async def verify_account(
        self,
        user_id: uuid.UUID,
        account_id: uuid.UUID,
        auth_payload: dict[str, Any] | None = None,
    ) -> GameAccount:
        """
        Trigger on-demand account verification using the platform adapter.
        """
        account = await self.get_account_by_id(user_id, account_id)

        if not self.registry.has_provider(account.platform):
            raise ValidationException(
                f"Platform '{account.platform}' does not have an active verification adapter."
            )

        provider = self.registry.get(account.platform)
        result: AccountVerificationResult = await provider.verify_account(
            account_identifier=account.account_identifier,
            auth_payload=auth_payload,
        )

        if not result.is_valid:
            raise ValidationException(
                result.error_message or "External account verification failed."
            )

        updated = await self.account_repo.update_sync_data(
            account_id=account.id,
            raw_data=result.metadata,
            in_game_name=result.in_game_name,
            tagline=result.tagline,
            region=result.region,
            is_verified=True,
        )
        return updated or account

    async def sync_account(
        self,
        user_id: uuid.UUID,
        account_id: uuid.UUID,
    ) -> tuple[GameAccount, list[PlayerStat], ProviderSyncResult]:
        """
        Perform full profile and telemetry synchronization via the registered GameProvider adapter.
        Persists updated profile information and upserts player statistics.
        """
        account = await self.get_account_by_id(user_id, account_id)

        if not self.registry.has_provider(account.platform):
            raise ValidationException(
                f"Platform '{account.platform}' does not have an active synchronization adapter."
            )

        provider = self.registry.get(account.platform)
        sync_result: ProviderSyncResult = await provider.sync(game_account=account)

        if not sync_result.is_success:
            raise ProviderException(
                sync_result.error_message or "Account synchronization failed at external provider.",
                platform=account.platform,
            )

        # 1. Update GameAccount metadata and raw telemetry
        in_game_name = sync_result.profile.in_game_name if sync_result.profile else None
        tagline = sync_result.profile.tagline if sync_result.profile else None
        region = sync_result.profile.region if sync_result.profile else None
        raw_data = sync_result.profile.raw_data if sync_result.profile else {}

        updated_account = await self.account_repo.update_sync_data(
            account_id=account.id,
            raw_data=raw_data,
            in_game_name=in_game_name,
            tagline=tagline,
            region=region,
            is_verified=True,
        ) or account

        # 2. Upsert PlayerStats records
        synced_stats: list[PlayerStat] = []
        for stat_data in sync_result.stats:
            stat_attributes = {
                "rank": stat_data.rank,
                "rank_tier": stat_data.rank_tier,
                "rank_rating": stat_data.rank_rating,
                "peak_rank": stat_data.peak_rank,
                "matches_played": stat_data.matches_played,
                "wins": stat_data.wins,
                "losses": stat_data.losses,
                "win_rate": stat_data.win_rate,
                "kd_ratio": stat_data.kd_ratio,
                "headshot_percentage": stat_data.headshot_percentage,
                "damage_per_round": stat_data.damage_per_round,
                "raw_stats_data": stat_data.raw_stats,
            }
            persisted_stat = await self.stat_repo.upsert_stat(
                game_account_id=account.id,
                user_id=user_id,
                season=stat_data.season,
                game_mode=stat_data.game_mode,
                stat_attributes=stat_attributes,
            )
            synced_stats.append(persisted_stat)

        return updated_account, synced_stats, sync_result

    async def get_account_stats(
        self,
        user_id: uuid.UUID,
        account_id: uuid.UUID,
    ) -> Sequence[PlayerStat]:
        """Fetch all competitive statistics records for a verified game account."""
        # Ensure account exists and belongs to user
        await self.get_account_by_id(user_id, account_id)
        return await self.stat_repo.get_by_account_id(account_id)

    async def update_account(
        self,
        user_id: uuid.UUID,
        account_id: uuid.UUID,
        payload: GameAccountUpdateRequest,
    ) -> GameAccount:
        """Partially update user-editable fields on a game account."""
        account = await self.get_account_by_id(user_id, account_id)

        if payload.in_game_name is not None:
            account.in_game_name = payload.in_game_name
        if payload.tagline is not None:
            account.tagline = payload.tagline
        if payload.region is not None:
            account.region = payload.region
        if payload.is_primary is not None and payload.is_primary:
            await self.set_primary_account(user_id, account_id)
            return account

        return await self.account_repo.update(account)

    async def set_primary_account(
        self,
        user_id: uuid.UUID,
        account_id: uuid.UUID,
    ) -> GameAccount:
        """Designate an account as primary for its game."""
        account = await self.get_account_by_id(user_id, account_id)
        updated = await self.account_repo.set_primary_account(
            user_id=user_id,
            account_id=account.id,
            game_name=account.game_name,
        )
        return updated or account

    async def unlink_account(
        self,
        user_id: uuid.UUID,
        account_id: uuid.UUID,
    ) -> bool:
        """Unlink and delete a game account and cascade-delete its statistics."""
        account = await self.get_account_by_id(user_id, account_id)
        await self.account_repo.delete(account)
        return True
