"""
Application configuration management using Pydantic Settings v2.
Loads settings from environment variables and .env files with strict validation.
"""

from functools import lru_cache
from typing import Annotated, Any

from pydantic import (
    BeforeValidator,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.constants import Environment


def parse_cors(v: Any) -> list[str] | str:
    """Parse CORS origins from a list or comma-separated string."""
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    """
    SquadSync application configuration settings.
    Inherits from Pydantic Settings v2 with automatic environment variable parsing.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --------------------------------------------------------------------------
    # Core Application Settings
    # --------------------------------------------------------------------------
    APP_NAME: str = "SquadSync"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False

    # --------------------------------------------------------------------------
    # API Routing & Versioning
    # --------------------------------------------------------------------------
    API_V1_STR: str = "/api/v1"
    ENABLE_SWAGGER: bool = True

    # --------------------------------------------------------------------------
    # Security & Cryptography (JWT & bcrypt)
    # --------------------------------------------------------------------------
    SECRET_KEY: str = "insecure-secret-key-change-in-production-min-32-chars-long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --------------------------------------------------------------------------
    # CORS Configuration
    # --------------------------------------------------------------------------
    BACKEND_CORS_ORIGINS: Annotated[list[str], BeforeValidator(parse_cors)] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*",
    ]

    # --------------------------------------------------------------------------
    # Steam & OpenDota Game Integration Settings
    # --------------------------------------------------------------------------
    STEAM_API_KEY: str | None = None
    STEAM_OPENID_URL: str = "https://steamcommunity.com/openid/login"
    STEAM_REALM: str = "http://localhost:8000"
    STEAM_RETURN_URL: str = "http://localhost:8000/api/v1/games/steam/callback"
    OPENDOTA_BASE_URL: str = "https://api.opendota.com/api"
    OPENDOTA_API_KEY: str | None = None

    # --------------------------------------------------------------------------
    # Riot Games & Riot Sign-On (RSO) Settings
    # --------------------------------------------------------------------------
    RIOT_API_KEY: str | None = None
    RIOT_CLIENT_ID: str | None = None
    RIOT_CLIENT_SECRET: str | None = None
    RIOT_REDIRECT_URI: str = "http://localhost:8000/api/v1/games/riot/callback"
    RIOT_RSO_AUTH_URL: str = "https://auth.riotgames.com/authorize"
    RIOT_RSO_TOKEN_URL: str = "https://auth.riotgames.com/token"
    RIOT_RSO_USERINFO_URL: str = "https://auth.riotgames.com/userinfo"
    RIOT_DEFAULT_REGION: str = "na"

    # --------------------------------------------------------------------------
    # NewsAPI.org Integration
    # --------------------------------------------------------------------------
    NEWS_API_KEY: str | None = None
    NEWS_API_BASE_URL: str = "https://newsapi.org/v2"
    # How many hours to consider cached articles still fresh before re-fetching
    NEWS_CACHE_TTL_HOURS: int = 1

    # --------------------------------------------------------------------------
    # Database Configuration (PostgreSQL / SQLite fallback)
    # --------------------------------------------------------------------------
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "squadsync_db"
    DATABASE_URL: str | None = "sqlite+aiosqlite:///./squadsync.db"

    # Connection Pool Settings
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Computed async database connection URL for SQLAlchemy 2.0.
        """
        if self.DATABASE_URL:
            if self.DATABASE_URL.startswith("postgresql://"):
                return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
            if self.DATABASE_URL.startswith("sqlite://"):
                return self.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://", 1)
            return self.DATABASE_URL

        return "sqlite+aiosqlite:///./squadsync.db"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SYNC_DATABASE_URI(self) -> str:
        """Synchronous URI used for Alembic migrations."""
        uri = self.SQLALCHEMY_DATABASE_URI
        if uri.startswith("postgresql+asyncpg://"):
            return uri.replace("postgresql+asyncpg://", "postgresql://", 1)
        return uri

    @property
    def is_development(self) -> bool:
        """Convenience flag for development environment."""
        return self.ENVIRONMENT == Environment.DEVELOPMENT

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        """Enforces strong cryptographic secrets in staging and production environments."""
        if self.ENVIRONMENT in (Environment.PRODUCTION, Environment.STAGING):
            if "insecure-secret-key" in self.SECRET_KEY or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "SECRET_KEY must be a cryptographically secure string of at least 32 characters in production/staging environments."
                )
        return self


@lru_cache
def get_settings() -> Settings:
    """Cached singleton instance of application settings."""
    return Settings()


# Primary settings instance
settings: Settings = get_settings()
