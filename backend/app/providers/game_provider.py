"""
Abstract Base Provider for Game Integration Framework.
Defines the Adapter interface required by all third-party gaming platform adapters
(e.g., Riot Games, Steam, Epic Games, Blizzard / Battle.net).
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from app.providers.dto import (
    AccountVerificationResult,
    ProviderProfileData,
    ProviderStatsData,
    ProviderSyncResult,
)

if TYPE_CHECKING:
    from app.models.game_account import GameAccount


class GameProvider(ABC):
    """
    Abstract Base Class defining the contract for game platform adapters.
    Subclasses must implement methods to communicate with specific publisher APIs,
    translating proprietary payloads into unified internal DTOs.
    """

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """
        Unique identifier for the gaming platform (e.g., 'riot', 'steam', 'epic', 'battlenet').
        """
        pass

    @property
    @abstractmethod
    def supported_games(self) -> list[str]:
        """
        List of game titles supported by this provider (e.g., ['Valorant', 'League of Legends']).
        """
        pass

    @abstractmethod
    async def verify_account(
        self,
        account_identifier: str,
        auth_payload: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AccountVerificationResult:
        """
        Verify the validity and ownership of an external gaming account.

        :param account_identifier: Unique external account ID (e.g., Riot PUUID, SteamID64).
        :param auth_payload: Optional credentials, tokens, or OAuth authorization codes.
        :param kwargs: Additional provider-specific parameters.
        :return: AccountVerificationResult containing validation status and verified handle.
        """
        pass

    @abstractmethod
    async def fetch_profile(
        self,
        account_identifier: str,
        region: str | None = None,
        **kwargs: Any,
    ) -> ProviderProfileData:
        """
        Retrieve external gamer profile metadata from publisher telemetry.

        :param account_identifier: Unique external account ID.
        :param region: Optional platform region (e.g., 'na', 'eu', 'kr').
        :param kwargs: Additional provider-specific parameters.
        :return: ProviderProfileData containing normalized profile details.
        """
        pass

    @abstractmethod
    async def fetch_stats(
        self,
        account_identifier: str,
        season: str | None = None,
        game_mode: str | None = None,
        region: str | None = None,
        **kwargs: Any,
    ) -> list[ProviderStatsData]:
        """
        Retrieve competitive telemetry, ranks, and performance statistics.

        :param account_identifier: Unique external account ID.
        :param season: Specific competitive split/season/act to query.
        :param game_mode: Specific mode (e.g., 'competitive', 'premier', 'ranked').
        :param region: Optional platform region.
        :param kwargs: Additional provider-specific parameters.
        :return: List of ProviderStatsData objects across modes or seasons.
        """
        pass

    @abstractmethod
    async def sync(
        self,
        game_account: "GameAccount",
        **kwargs: Any,
    ) -> ProviderSyncResult:
        """
        Orchestrate a complete synchronization cycle for a linked GameAccount:
        fetches latest profile and telemetry stats, standardizes payloads,
        and packages them for persistence.

        :param game_account: The linked GameAccount domain model instance.
        :param kwargs: Additional provider-specific parameters.
        :return: ProviderSyncResult containing updated profile and batch of stats.
        """
        pass
