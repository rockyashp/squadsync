"""
Game Integration Framework custom exceptions.
"""

from typing import Any


class ProviderException(Exception):
    """Base exception for all game provider integration errors."""

    def __init__(self, message: str, platform: str | None = None, details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.platform = platform
        self.details = details


class ProviderNotFoundException(ProviderException):
    """Raised when an adapter for a requested gaming platform is not registered."""
    pass


class ProviderAuthException(ProviderException):
    """Raised when third-party provider API authentication or token verification fails."""
    pass


class ProviderRateLimitException(ProviderException):
    """Raised when external game publisher API rate limits are encountered."""
    pass


class ProviderAPIException(ProviderException):
    """Raised when external game publisher API returns an unexpected error or server fault."""
    pass


class AccountVerificationException(ProviderException):
    """Raised when external account credentials or identity verification fails."""
    pass
