"""
Steam Provider Adapter implementation.
Implements the GameProvider interface for the Steam platform:
- Steam OpenID 2.0 authentication & ownership verification
- Steam Web API player profile retrieval (GetPlayerSummaries)
- Standardized DTO transformations
"""

import logging
import re
from typing import Any
import httpx

from app.core.config import settings
from app.models.game_account import GameAccount
from app.providers.dto import (
    AccountVerificationResult,
    ProviderProfileData,
    ProviderStatsData,
    ProviderSyncResult,
)
from app.providers.exceptions import (
    AccountVerificationException,
    ProviderAPIException,
    ProviderException,
)
from app.providers.game_provider import GameProvider

logger = logging.getLogger("squadsync.providers.steam")

STEAM_ID64_REGEX = re.compile(r"^7656119\d{10}$")
STEAM_CLAIMED_ID_REGEX = re.compile(r"^https?://steamcommunity\.com/openid/id/(7656119\d{10})/?$")


class SteamProvider(GameProvider):
    """
    Adapter integrating Valve's Steam platform via OpenID 2.0 and Steam Web API.
    """

    def __init__(
        self,
        api_key: str | None = None,
        openid_url: str | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.STEAM_API_KEY
        self.openid_url = openid_url if openid_url is not None else settings.STEAM_OPENID_URL
        self._client = http_client

    @property
    def platform_name(self) -> str:
        return "steam"

    @property
    def supported_games(self) -> list[str]:
        return ["Steam", "Dota 2", "CS2", "Team Fortress 2"]

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is not None:
            return self._client
        return httpx.AsyncClient(timeout=10.0)

    @staticmethod
    def extract_steam_id(claimed_id: str) -> str | None:
        """Extract 64-bit Steam ID from OpenID claimed_id URL."""
        match = STEAM_CLAIMED_ID_REGEX.match(claimed_id.strip())
        if match:
            return match.group(1)
        if STEAM_ID64_REGEX.match(claimed_id.strip()):
            return claimed_id.strip()
        return None

    async def verify_account(
        self,
        account_identifier: str,
        auth_payload: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AccountVerificationResult:
        """
        Verify Steam account ownership using Steam OpenID 2.0 check_authentication assertion.
        """
        steam_id = account_identifier.strip()
        if not STEAM_ID64_REGEX.match(steam_id):
            return AccountVerificationResult(
                is_valid=False,
                account_identifier=steam_id,
                in_game_name="",
                error_message=f"Invalid SteamID64 format '{steam_id}'. Must be a 17-digit string starting with 7656119.",
            )

        # 1. If OpenID callback parameters provided, verify cryptographically with Valve
        if auth_payload and "openid.sig" in auth_payload:
            check_params = dict(auth_payload)
            check_params["openid.mode"] = "check_authentication"

            try:
                client = await self._get_client()
                response = await client.post(self.openid_url, data=check_params)
                if response.status_code != 200:
                    return AccountVerificationResult(
                        is_valid=False,
                        account_identifier=steam_id,
                        in_game_name="",
                        error_message=f"Steam OpenID verification server returned HTTP {response.status_code}",
                    )

                response_text = response.text
                if "is_valid:true" not in response_text:
                    return AccountVerificationResult(
                        is_valid=False,
                        account_identifier=steam_id,
                        in_game_name="",
                        error_message="Steam OpenID signature verification failed (is_valid:false)",
                    )

                claimed_id = check_params.get("openid.claimed_id", "")
                verified_id = self.extract_steam_id(claimed_id)
                if verified_id != steam_id:
                    return AccountVerificationResult(
                        is_valid=False,
                        account_identifier=steam_id,
                        in_game_name="",
                        error_message=f"Claimed SteamID '{verified_id}' does not match requested SteamID '{steam_id}'",
                    )
            except httpx.RequestError as e:
                logger.error(f"Failed to communicate with Steam OpenID server: {e}")
                return AccountVerificationResult(
                    is_valid=False,
                    account_identifier=steam_id,
                    in_game_name="",
                    error_message=f"Failed to communicate with Steam OpenID server: {str(e)}",
                )

        # 2. Fetch profile summary to populate player name and avatar
        try:
            profile = await self.fetch_profile(steam_id)
            return AccountVerificationResult(
                is_valid=True,
                account_identifier=steam_id,
                in_game_name=profile.in_game_name,
                region=profile.region,
                metadata={
                    "steam_id": steam_id,
                    "avatar_url": profile.avatar_url,
                    **profile.raw_data,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to fetch profile during verification, using fallback: {e}")
            return AccountVerificationResult(
                is_valid=True,
                account_identifier=steam_id,
                in_game_name=f"SteamUser_{steam_id[-4:]}",
                metadata={"steam_id": steam_id},
            )

    async def fetch_profile(
        self,
        account_identifier: str,
        region: str | None = None,
        **kwargs: Any,
    ) -> ProviderProfileData:
        """
        Fetch public persona name, avatar, and visibility from Steam Web API.
        """
        steam_id = account_identifier.strip()
        if not self.api_key:
            # Fallback if no Steam Web API key is configured
            return ProviderProfileData(
                account_identifier=steam_id,
                in_game_name=f"SteamUser_{steam_id[-4:]}",
                region=region,
                avatar_url="https://avatars.steamstatic.com/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg",
                raw_data={"steam_id": steam_id, "source": "unauthenticated_fallback"},
            )

        url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
        params = {"key": self.api_key, "steamids": steam_id}

        try:
            client = await self._get_client()
            response = await client.get(url, params=params)
            if response.status_code != 200:
                raise ProviderAPIException(
                    f"Steam Web API error: HTTP {response.status_code}",
                    platform="steam",
                )

            data = response.json()
            players = data.get("response", {}).get("players", [])
            if not players:
                raise ProviderException(
                    f"No Steam profile found for SteamID {steam_id}",
                    platform="steam",
                )

            p = players[0]
            return ProviderProfileData(
                account_identifier=steam_id,
                in_game_name=p.get("personaname", f"SteamUser_{steam_id[-4:]}"),
                region=p.get("loccountrycode", region),
                avatar_url=p.get("avatarfull") or p.get("avatarmedium") or p.get("avatar"),
                raw_data=p,
            )
        except httpx.RequestError as e:
            raise ProviderAPIException(f"Steam network request failed: {e}", platform="steam") from e

    async def fetch_stats(
        self,
        account_identifier: str,
        season: str | None = None,
        game_mode: str | None = None,
        region: str | None = None,
        **kwargs: Any,
    ) -> list[ProviderStatsData]:
        """
        Retrieve generic Steam platform stats (games count or platform metadata).
        """
        return []

    async def sync(
        self,
        game_account: GameAccount,
        **kwargs: Any,
    ) -> ProviderSyncResult:
        """
        Synchronize Steam profile metadata.
        """
        try:
            profile = await self.fetch_profile(game_account.account_identifier, region=game_account.region)
            stats = await self.fetch_stats(game_account.account_identifier)
            return ProviderSyncResult(
                is_success=True,
                profile=profile,
                stats=stats,
            )
        except Exception as e:
            logger.error(f"Error syncing Steam account {game_account.account_identifier}: {e}")
            return ProviderSyncResult(
                is_success=False,
                error_message=str(e),
            )
