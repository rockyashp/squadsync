"""
Game Provider Registry for runtime adapter discovery and injection.
Implements a decoupled registry pattern conforming to Open/Closed Principle.
"""

from app.providers.exceptions import ProviderNotFoundException
from app.providers.game_provider import GameProvider


class GameProviderRegistry:
    """
    Registry for managing available third-party GameProvider adapters.
    Allows runtime registration and resolution of platform adapters without modifying core services.
    """

    def __init__(self) -> None:
        self._providers: dict[str, GameProvider] = {}

    def register(self, platform: str, provider: GameProvider) -> None:
        """
        Register a new platform adapter instance.
        Keys are normalized to lowercase.
        """
        normalized_platform = platform.strip().lower()
        self._providers[normalized_platform] = provider

    def get(self, platform: str) -> GameProvider:
        """
        Retrieve the registered provider adapter for a platform.
        Raises ProviderNotFoundException if no adapter is registered.
        """
        normalized_platform = platform.strip().lower()
        provider = self._providers.get(normalized_platform)
        if not provider:
            supported = ", ".join(self._providers.keys()) or "none"
            raise ProviderNotFoundException(
                f"No game provider registered for platform '{platform}'. "
                f"Available platforms: [{supported}].",
                platform=normalized_platform,
            )
        return provider

    def has_provider(self, platform: str) -> bool:
        """Check whether an adapter is registered for the specified platform."""
        return platform.strip().lower() in self._providers

    def list_supported_platforms(self) -> list[str]:
        """Return a list of all registered platform keys."""
        return sorted(self._providers.keys())

    def clear(self) -> None:
        """Clear all registered providers (primarily used for test teardown)."""
        self._providers.clear()


def create_default_registry() -> GameProviderRegistry:
    """Instantiate and configure default game platform adapters."""
    reg = GameProviderRegistry()
    from app.providers.opendota_provider import OpenDotaProvider
    from app.providers.riot_provider import RiotProvider
    from app.providers.steam_provider import SteamProvider

    reg.register("steam", SteamProvider())
    reg.register("opendota", OpenDotaProvider())
    reg.register("dota2", OpenDotaProvider())
    reg.register("riot", RiotProvider())
    reg.register("valorant", RiotProvider())
    return reg


# Global default registry instance with out-of-the-box adapters
provider_registry = create_default_registry()
