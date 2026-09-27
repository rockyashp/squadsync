"""
Riot Games domain service implementation.
Coordinates Riot Sign-On (RSO) authorization, code verification, account linking,
Valorant competitive telemetry fetching, and PostgreSQL JSONB persistence:
- PUUID
- Summoner Name
- Rank
- Current Season
- Preferred Agent
- Competitive Tier
"""

from collections.abc import Sequence
from datetime import datetime, timezone
import logging
from typing import Any
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    EntityNotFoundException,
    ValidationException,
)
from app.models.game_account import GameAccount
from app.models.player_stat import PlayerStat
from app.providers.riot_provider import (
    RiotProvider,
    format_valorant_tier,
)
from app.repositories.game_account_repository import GameAccountRepository
from app.repositories.player_stat_repository import PlayerStatRepository
from app.schemas.riot import (
    RiotLoginUrlResponse,
    RiotSyncResponse,
)

logger = logging.getLogger("squadsync.services.riot")


class RiotService:
    """
    Domain service for Riot Games (Valorant) integration and Riot Sign-On (RSO) flows.
    """

    def __init__(
        self,
        db: AsyncSession,
        account_repo: GameAccountRepository | None = None,
        stat_repo: PlayerStatRepository | None = None,
        riot_provider: RiotProvider | None = None,
    ) -> None:
        self.db = db
        self.account_repo = account_repo or GameAccountRepository(db)
        self.stat_repo = stat_repo or PlayerStatRepository(db)
        self.riot_provider = riot_provider or RiotProvider()

    def get_rso_login_url(self, state: str | None = None) -> RiotLoginUrlResponse:
        """
        Generate Riot Sign-On (RSO) OAuth2 redirect URL.
        """
        auth_url = self.riot_provider.get_authorization_url(state=state)
        return RiotLoginUrlResponse(
            auth_url=auth_url,
            client_id_configured=bool(self.riot_provider.client_id),
            redirect_uri=self.riot_provider.redirect_uri,
            state=state,
        )

    async def handle_rso_callback(
        self,
        user_id: uuid.UUID,
        code: str,
        state: str | None = None,
    ) -> GameAccount:
        """
        Exchange RSO code for tokens, verify player identity via /userinfo,
        and link/verify the Riot GameAccount.
        """
        verification = await self.riot_provider.verify_account(
            account_identifier="",
            auth_payload={"code": code, "state": state},
        )

        if not verification.is_valid:
            raise ValidationException(
                verification.error_message or "Riot Sign-On authentication verification failed"
            )

        puuid = verification.account_identifier
        now = datetime.now(timezone.utc)

        # Check if user already linked this PUUID
        existing = await self.account_repo.get_user_account_by_platform(
            user_id=user_id,
            platform="riot",
            account_identifier=puuid,
        )

        if existing:
            existing.is_verified = True
            existing.last_synced_at = now
            if verification.in_game_name:
                existing.in_game_name = verification.in_game_name
            if verification.tagline:
                existing.tagline = verification.tagline
            await self.account_repo.update(existing)
            return existing

        # Create new verified GameAccount
        new_account = GameAccount(
            user_id=user_id,
            game_name="Valorant",
            platform="riot",
            account_identifier=puuid,
            in_game_name=verification.in_game_name or f"RiotPlayer_{puuid[:6]}",
            tagline=verification.tagline or "NA1",
            region=verification.region or "na",
            is_verified=True,
            is_primary=True,
            raw_profile_data=verification.metadata,
            last_synced_at=now,
        )

        return await self.account_repo.create(new_account)

    async def get_or_create_riot_account(
        self,
        user_id: uuid.UUID,
        puuid: str,
    ) -> GameAccount:
        """Helper to resolve or instantiate a Riot account for a user."""
        account = await self.account_repo.get_user_account_by_platform(
            user_id=user_id,
            platform="riot",
            account_identifier=puuid.strip(),
        )
        if not account:
            account = GameAccount(
                user_id=user_id,
                game_name="Valorant",
                platform="riot",
                account_identifier=puuid.strip(),
                in_game_name=f"RiotPlayer_{puuid.strip()[:6]}",
                tagline="NA1",
                is_verified=False,
                is_primary=True,
            )
            account = await self.account_repo.create(account)
        return account

    async def sync_riot_account(
        self,
        user_id: uuid.UUID,
        account_id: uuid.UUID | None = None,
        puuid: str | None = None,
        **kwargs: Any,
    ) -> RiotSyncResponse:
        """
        Synchronize competitive telemetry for Riot Games (Valorant):
        - PUUID
        - Summoner Name
        - Rank
        - Current Season
        - Preferred Agent
        - Competitive Tier
        - Captures raw API response inside PostgreSQL JSONB
        """
        # Resolve target account
        account: GameAccount | None = None
        if account_id:
            account = await self.account_repo.get_by_id(account_id)
            if not account or account.user_id != user_id:
                raise EntityNotFoundException(f"Game account with ID '{account_id}' not found.")
        elif puuid:
            account = await self.get_or_create_riot_account(user_id, puuid)
        else:
            accounts = await self.account_repo.get_by_user_and_game(user_id, "Valorant")
            if accounts:
                account = accounts[0]
            else:
                raise EntityNotFoundException("No linked Riot/Valorant account found for this user.")

        # 1. Coordinate sync via RiotProvider
        sync_result = await self.riot_provider.sync(game_account=account, **kwargs)
        if not sync_result.is_success or not sync_result.stats:
            raise ValidationException(
                sync_result.error_message or "Failed to synchronize telemetry from Riot Games."
            )

        stat_dto = sync_result.stats[0]
        telemetry: dict[str, Any] = stat_dto.raw_stats or {}

        # 2. Extract required normalized metrics
        target_puuid = telemetry.get("puuid", account.account_identifier)
        summoner_name = telemetry.get("summoner_name", account.in_game_name)
        rank = telemetry.get("rank", format_valorant_tier(stat_dto.rank_tier))
        current_season = telemetry.get("current_season", stat_dto.season)
        preferred_agent = telemetry.get("preferred_agent", "Jett")
        competitive_tier = int(telemetry.get("competitive_tier", stat_dto.rank_tier or 0))
        wins = int(telemetry.get("wins", stat_dto.wins))
        losses = int(telemetry.get("losses", stat_dto.losses))
        win_rate = float(telemetry.get("win_rate", stat_dto.win_rate or 0.0))

        # 3. Update GameAccount metadata & raw telemetry JSONB
        now = datetime.now(timezone.utc)
        account.in_game_name = summoner_name
        account.last_synced_at = now
        account.raw_profile_data = telemetry
        await self.account_repo.update(account)

        # 4. Upsert PlayerStat competitive record
        stat_attributes = {
            "rank": rank,
            "rank_tier": competitive_tier,
            "rank_rating": stat_dto.rank_rating or 0,
            "matches_played": stat_dto.matches_played,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "kd_ratio": stat_dto.kd_ratio or 0.0,
            "raw_stats_data": telemetry,
        }
        await self.stat_repo.upsert_stat(
            game_account_id=account.id,
            user_id=user_id,
            season=current_season,
            game_mode=stat_dto.game_mode,
            stat_attributes=stat_attributes,
        )

        return RiotSyncResponse(
            account_id=account.id,
            user_id=user_id,
            puuid=target_puuid,
            summoner_name=summoner_name,
            rank=rank,
            current_season=current_season,
            preferred_agent=preferred_agent,
            competitive_tier=competitive_tier,
            wins=wins,
            losses=losses,
            win_rate=win_rate,
            is_verified=account.is_verified,
            last_synced_at=now,
            raw_profile_data=telemetry,
        )

    async def get_riot_profile(self, user_id: uuid.UUID) -> RiotSyncResponse:
        """
        Retrieve cached synchronized Riot profile, competitive tier, and agent metrics.
        """
        accounts = await self.account_repo.get_by_user_and_game(user_id, "Valorant")
        if not accounts:
            raise EntityNotFoundException("No linked Riot/Valorant account found for this user.")

        account = accounts[0]
        telemetry = account.raw_profile_data or {}

        competitive_tier = int(telemetry.get("competitive_tier", 0))
        return RiotSyncResponse(
            account_id=account.id,
            user_id=user_id,
            puuid=account.account_identifier,
            summoner_name=account.in_game_name,
            rank=telemetry.get("rank", format_valorant_tier(competitive_tier)),
            current_season=telemetry.get("current_season", "Episode 8: Act 3"),
            preferred_agent=telemetry.get("preferred_agent", "Jett"),
            competitive_tier=competitive_tier,
            wins=int(telemetry.get("wins", 0)),
            losses=int(telemetry.get("losses", 0)),
            win_rate=float(telemetry.get("win_rate", 0.0)),
            is_verified=account.is_verified,
            last_synced_at=account.last_synced_at or datetime.now(timezone.utc),
            raw_profile_data=telemetry,
        )
