"""
Global constants and enumerations for the SquadSync application.
"""

from enum import StrEnum


class Environment(StrEnum):
    """Application deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class TokenTypes(StrEnum):
    """JWT Token types."""
    ACCESS = "access"
    REFRESH = "refresh"
    PASSWORD_RESET = "password_reset"


# API Defaults
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Error Messages
DB_CONNECTION_ERROR_MSG = "Database connectivity check failed."
UNAUTHORIZED_ERROR_MSG = "Could not validate credentials."
FORBIDDEN_ERROR_MSG = "Not enough permissions to access this resource."
