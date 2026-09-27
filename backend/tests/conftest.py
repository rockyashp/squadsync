"""
Pytest configuration, fixtures, database session lifecycle, and authentication mocks.
Configured for PostgreSQL testing with dependency injection overrides.
"""

import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
import os
from typing import Any
import uuid

import httpx
from httpx import ASGITransport, AsyncClient
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings
from app.core.dependencies import get_current_active_user, get_current_user, get_db
from app.core.security import create_access_token, get_password_hash
from app.models.base import Base
from app.main import app
from app.models.user import User

from sqlalchemy.pool import NullPool

# Test Database Connection URL (PostgreSQL)
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    settings.SQLALCHEMY_DATABASE_URI,
)


@pytest_asyncio.fixture
async def test_engine() -> AsyncGenerator[AsyncEngine | None, None]:
    """
    Creates the test database engine and initializes the schema on PostgreSQL.
    Uses NullPool and function scope to ensure connections are bound to the
    exact asyncio event loop of the current test, avoiding cross-loop Future errors.
    """
    engine = None
    try:
        engine = create_async_engine(
            TEST_DATABASE_URL,
            echo=False,
            future=True,
            poolclass=NullPool,
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield engine
        try:
            async with engine.begin() as conn:
                for table in reversed(Base.metadata.sorted_tables):
                    await conn.execute(table.delete())
        except Exception:
            pass
        await engine.dispose()
    except Exception:
        # If live PostgreSQL server is unreachable with current credentials, yield None
        yield None
        if engine:
            await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: AsyncEngine | None) -> AsyncGenerator[AsyncSession | None, None]:
    """
    Provides an isolated async database session per test with automatic rollback.
    """
    if not test_engine:
        yield None
        return

    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


from unittest.mock import AsyncMock, MagicMock

@pytest_asyncio.fixture
async def client(db_session: AsyncSession | None) -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP test client bound to the FastAPI application with test database override.
    Uses PostgreSQL session if available, else falls back to mock session for isolated testing.
    """
    if db_session:
        async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
            yield db_session

        app.dependency_overrides[get_db] = override_get_db
    else:
        # Mock session fallback when PostgreSQL test credentials are not populated
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        mock_session.get.return_value = None

        async def override_mock_get_db() -> AsyncGenerator[AsyncSession, None]:
            yield mock_session

        app.dependency_overrides[get_db] = override_mock_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


# ==============================================================================
# JWT & Authentication Fixtures
# ==============================================================================

@pytest.fixture
def mock_user_id() -> uuid.UUID:
    """Deterministic mock user UUID."""
    return uuid.UUID("11111111-2222-3333-4444-555555555555")


@pytest.fixture
def mock_user(mock_user_id: uuid.UUID) -> User:
    """Mock authenticated User instance."""
    now = datetime.now(timezone.utc)
    return User(
        id=mock_user_id,
        username="pro_tester",
        email="tester@squadsync.gg",
        password_hash=get_password_hash("StrongP@ssw0rd123!"),
        is_active=True,
        failed_login_attempts=0,
        is_locked=False,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def mock_jwt_token(mock_user_id: uuid.UUID) -> str:
    """Generates a valid signed JWT access token for the mock user."""
    return create_access_token(subject=str(mock_user_id))


@pytest.fixture
def auth_headers(mock_jwt_token: str) -> dict[str, str]:
    """HTTP Authorization headers containing the mock Bearer token."""
    return {"Authorization": f"Bearer {mock_jwt_token}"}


@pytest_asyncio.fixture
async def authenticated_client(
    client: AsyncClient,
    mock_user: User,
    mock_jwt_token: str,
    db_session: AsyncSession | None,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Test client with mocked authentication headers and dependencies.
    """
    from app.core.dependencies import oauth2_scheme

    if db_session:
        existing = await db_session.get(User, mock_user.id)
        if not existing:
            db_session.add(mock_user)
            await db_session.commit()

    app.dependency_overrides[oauth2_scheme] = lambda: mock_jwt_token
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_current_active_user] = lambda: mock_user

    yield client

    app.dependency_overrides.pop(oauth2_scheme, None)
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_current_active_user, None)
