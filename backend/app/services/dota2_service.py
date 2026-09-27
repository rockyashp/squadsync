"""
Dota 2 and Steam domain service implementation.
Coordinates Steam OpenID authentication URL creation, OpenID assertion verification,
account linking, OpenDota telemetry fetching, and background synchronization tasks.
"""

from collections.abc import Sequence
from datetime import datetime, timezone
import logging
from typing import Any
from urllib.parse import urlencode
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import async_session_factory
from app.core.exceptions import (
    EntityNotFoundException,
    ValidationException,
)
from app.models.game_account import GameAccount
from app.models.player_stat import PlayerStat
from app.providers.opendota_provider import (
    OpenDotaProvider,
    format_rank_tier,
    steam_id64_to_dota_id,
)
from app.providers.steam_provider import SteamProvider
from app.repositories.game_account_repository import GameAccountRepository
from app.repositories.player_stat_repository import PlayerStatRepository
from app.schemas.dota2 import (
    Dota2HeroStat,
    Dota2RecentMatch,
    Dota2SyncResponse,
    SteamLoginUrlResponse,
)

logger = logging.getLogger("squadsync.services.dota2")


class Dota2Service:
    """
    Domain service for Steam Authentication and Dota 2 OpenDota integration.
    """

    def __init__(
        self,
        db: AsyncSession,
        account_repo: GameAccountRepository | None = None,
        stat_repo: PlayerStatRepository | None = None,
        steam_provider: SteamProvider | None = None,
        opendota_provider: OpenDotaProvider | None = None,
    ) -> None:
        self.db = db
        self.account_repo = account_repo or GameAccountRepository(db)
        self.stat_repo = stat_repo or PlayerStatRepository(db)
        self.steam_provider = steam_provider or SteamProvider()
        self.opendota_provider = opendota_provider or OpenDotaProvider()

    def get_steam_login_url(self, return_to: str | None = None) -> SteamLoginUrlResponse:
        """
        Construct Steam OpenID 2.0 authentication URL.
        """
        realm = settings.STEAM_REALM
        callback_url = return_to or settings.STEAM_RETURN_URL

        params = {
            "openid.ns": "http://specs.openid.net/auth/2.0",
            "openid.mode": "checkid_setup",
            "openid.return_to": callback_url,
            "openid.realm": realm,
            "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
        }

        full_url = f"{settings.STEAM_OPENID_URL}?{urlencode(params)}"
        return SteamLoginUrlResponse(
            login_url=full_url,
            realm=realm,
            return_to=callback_url,
        )

    async def verify_and_link_steam(
        self,
        user_id: uuid.UUID,
        openid_params: dict[str, Any],
    ) -> GameAccount:
        """
        Verify Steam OpenID authentication assertion, extract SteamID64,
        and link/update the user's Dota 2 GameAccount.
        """
        claimed_id = openid_params.get("openid.claimed_id", "")
        steam_id = SteamProvider.extract_steam_id(claimed_id)
        if not steam_id:
            raise ValidationException("Invalid or missing openid.claimed_id in Steam OpenID callback")

        # 1. Cryptographically verify signature with Valve OpenID endpoint
        verification = await self.steam_provider.verify_account(
            account_identifier=steam_id,
            auth_payload=openid_params,
        )

        if not verification.is_valid:
            raise ValidationException(
                verification.error_message or "Steam OpenID ownership verification failed"
            )

        # 2. Check if user already linked this Steam ID
        existing = await self.account_repo.get_user_account_by_platform(
            user_id=user_id,
            platform="steam",
            account_identifier=steam_id,
        )

        now = datetime.now(timezone.utc)
        if existing:
            existing.is_verified = True
            existing.last_synced_at = now
            if verification.in_game_name:
                existing.in_game_name = verification.in_game_name
            await self.account_repo.update(existing)
            return existing

        # 3. Create newly verified GameAccount
        new_account = GameAccount(
            user_id=user_id,
            game_name="Dota 2",
            platform="steam",
            account_identifier=steam_id,
            in_game_name=verification.in_game_name or f"DotaGamer_{steam_id[-4:]}",
            tagline=None,
            region=verification.region,
            is_verified=True,
            is_primary=True,
            raw_profile_data=verification.metadata,
            last_synced_at=now,
        )

        return await self.account_repo.create(new_account)

    async def get_or_create_dota_account(
        self,
        user_id: uuid.UUID,
        steam_id: str,
    ) -> GameAccount:
        """Helper to resolve or instantiate a Steam/Dota 2 account for a user."""
        account = await self.account_repo.get_user_account_by_platform(
            user_id=user_id,
            platform="steam",
            account_identifier=steam_id.strip(),
        )
        if not account:
            account = GameAccount(
                user_id=user_id,
                game_name="Dota 2",
                platform="steam",
                account_identifier=steam_id.strip(),
                in_game_name=f"DotaUser_{steam_id.strip()[-4:]}",
                is_verified=False,
                is_primary=True,
            )
            account = await self.account_repo.create(account)
        return account

    async def sync_dota2_account(
        self,
        user_id: uuid.UUID,
        account_id: uuid.UUID | None = None,
        steam_id: str | None = None,
        sync_mode: str = "realtime",
    ) -> Dota2SyncResponse:
        """
        Synchronize Dota 2 telemetry via OpenDota:
        - Fetches MMR, rank, wins/losses, favorite heroes, and recent matches
        - Normalizes all telemetry into standard schemas
        - Stores the full raw response payload in PostgreSQL JSONB
        - Upserts competitive PlayerStat record
        """
        # Resolve target account
        account: GameAccount | None = None
        if account_id:
            account = await self.account_repo.get_by_id(account_id)
            if not account or account.user_id != user_id:
                raise EntityNotFoundException(f"Game account with ID '{account_id}' not found.")
        elif steam_id:
            account = await self.get_or_create_dota_account(user_id, steam_id)
        else:
            # Look for existing primary Dota 2 account for this user
            accounts = await self.account_repo.get_by_user_and_game(user_id, "Dota 2")
            if accounts:
                account = accounts[0]
            else:
                raise EntityNotFoundException("No linked Steam/Dota 2 account found for this user.")

        # 1. Fetch telemetry via OpenDotaProvider
        sync_result = await self.opendota_provider.sync(game_account=account)
        if not sync_result.is_success or not sync_result.stats:
            raise ValidationException(
                sync_result.error_message or "Failed to synchronize Dota 2 telemetry from OpenDota."
            )

        stat_dto = sync_result.stats[0]
        telemetry: dict[str, Any] = stat_dto.raw_stats or {}

        # 2. Extract normalized properties
        player_name = (
            sync_result.profile.in_game_name
            if sync_result.profile
            else telemetry.get("player_name", account.in_game_name)
        )
        avatar_url = (
            sync_result.profile.avatar_url
            if sync_result.profile
            else telemetry.get("avatar")
        )
        mmr = telemetry.get("mmr")
        rank = telemetry.get("rank", "Unranked")
        wins = int(telemetry.get("wins", 0))
        losses = int(telemetry.get("losses", 0))

        # 3. Parse Favorite Heroes
        raw_fav_heroes = telemetry.get("favorite_heroes", [])
        favorite_heroes = [Dota2HeroStat(**h) for h in raw_fav_heroes]

        # 4. Parse Recent Matches
        raw_matches = telemetry.get("recent_matches", [])
        recent_matches = [Dota2RecentMatch(**m) for m in raw_matches]

        # 5. Persist raw API payload & normalized fields on GameAccount
        now = datetime.now(timezone.utc)
        account.in_game_name = player_name
        account.last_synced_at = now
        account.raw_profile_data = telemetry
        await self.account_repo.update(account)

        # 6. Upsert PlayerStat competitive record
        stat_attributes = {
            "rank": rank,
            "rank_tier": telemetry.get("rank_tier"),
            "rank_rating": mmr,
            "matches_played": wins + losses,
            "wins": wins,
            "losses": losses,
            "win_rate": telemetry.get("win_rate", 0.0),
            "kd_ratio": stat_dto.kd_ratio or 0.0,
            "raw_stats_data": telemetry,
        }
        await self.stat_repo.upsert_stat(
            game_account_id=account.id,
            user_id=user_id,
            season="Current",
            game_mode="ranked",
            stat_attributes=stat_attributes,
        )

        return Dota2SyncResponse(
            account_id=account.id,
            user_id=user_id,
            steam_id=account.account_identifier,
            player_name=player_name,
            avatar=avatar_url,
            mmr=mmr,
            rank=rank,
            wins=wins,
            losses=losses,
            favorite_heroes=favorite_heroes,
            recent_matches=recent_matches,
            is_verified=account.is_verified,
            last_synced_at=now,
            sync_mode=sync_mode,
            raw_profile_data=telemetry,
        )

    async def get_dota2_profile(self, user_id: uuid.UUID) -> Dota2SyncResponse:
        """
        Retrieve existing synchronized Dota 2 profile and competitive stats for user.
        """
        accounts = await self.account_repo.get_by_user_and_game(user_id, "Dota 2")
        if not accounts:
            raise EntityNotFoundException("No linked Dota 2 account found for this user.")

        account = accounts[0]
        telemetry = account.raw_profile_data or {}

        favorite_heroes = [
            Dota2HeroStat(**h) for h in telemetry.get("favorite_heroes", [])
        ]
        recent_matches = [
            Dota2RecentMatch(**m) for m in telemetry.get("recent_matches", [])
        ]

        return Dota2SyncResponse(
            account_id=account.id,
            user_id=user_id,
            steam_id=account.account_identifier,
            player_name=account.in_game_name,
            avatar=telemetry.get("avatar"),
            mmr=telemetry.get("mmr"),
            rank=telemetry.get("rank", "Unranked"),
            wins=telemetry.get("wins", 0),
            losses=telemetry.get("losses", 0),
            favorite_heroes=favorite_heroes,
            recent_matches=recent_matches,
            is_verified=account.is_verified,
            last_synced_at=account.last_synced_at or datetime.now(timezone.utc),
            sync_mode="cached",
            raw_profile_data=telemetry,
        )


async def run_background_dota2_sync(user_id: uuid.UUID, account_id: uuid.UUID) -> None:
    """
    Background worker function for asynchronous telemetry refresh without blocking HTTP requests.
    """
    logger.info(f"Starting background Dota 2 sync for user {user_id}, account {account_id}")
    async with async_session_factory() as db:
        service = Dota2Service(db)
        try:
            await service.sync_dota2_account(
                user_id=user_id,
                account_id=account_id,
                sync_mode="background",
            )
            logger.info(f"Background Dota 2 sync completed successfully for account {account_id}")
        except Exception as e:
            logger.error(f"Background Dota 2 sync failed for account {account_id}: {e}")
