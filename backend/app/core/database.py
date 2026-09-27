"""
SQLAlchemy 2.0 async database configuration, connection pooling, and session dependency.
"""

from collections.abc import AsyncGenerator
import logging

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

logger = logging.getLogger(__name__)

if settings.SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
    engine: AsyncEngine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        echo=settings.DB_ECHO,
        future=True,
        connect_args={"check_same_thread": False},
    )
else:
    engine: AsyncEngine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        echo=settings.DB_ECHO,
        future=True,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_pre_ping=True,
    )

# Async Sessionmaker factory
AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Standard alias
async_session_factory = AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency providing an isolated async database session per request.
    Rolls back transaction on unhandled exception and guarantees session closure.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db_connection() -> None:
    """Disposes database engine pool upon application teardown."""
    logger.info("Disposing database connection pool...")
    await engine.dispose()
    logger.info("Database connection pool disposed.")
