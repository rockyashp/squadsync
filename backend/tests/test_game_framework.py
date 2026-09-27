"""
Tests for Game Integration Framework and Adapter Pattern:
- Abstract GameProvider class contract and instantiation constraints
- GameProviderRegistry registration, resolution, and error handling
- GameAccount and PlayerStat schema validation
- GameService domain logic (linking, verification, synchronization, telemetry persistence, unlinking)
- Game API endpoints authorization and responses
"""

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock
import uuid

from httpx import AsyncClient
import pytest

from app.core.exceptions import ConflictException, EntityNotFoundException, ValidationException
from app.models.game_account import GameAccount
from app.models.player_stat import PlayerStat
from app.models.user import User
from app.providers.dto import (
    AccountVerificationResult,
    ProviderProfileData,
    ProviderStatsData,
    ProviderSyncResult,
)
from app.providers.exceptions import ProviderException, ProviderNotFoundException
from app.providers.game_provider import GameProvider
from app.providers.registry import GameProviderRegistry
from app.schemas.game_account import (
    GameAccountLinkRequest,
    GameAccountRead,
    GameAccountUpdateRequest,
    PlayerStatRead,
)
from app.services.game_service import GameService


# ==============================================================================
# Concrete Mock Provider Adapter for testing
# ==============================================================================

class MockRiotAdapter(GameProvider):
    """Concrete mock adapter simulating a Riot Games API integration."""

    @property
    def platform_name(self) -> str:
        return "riot"

    @property
    def supported_games(self) -> list[str]:
        return ["Valorant", "League of Legends"]

    async def verify_account(
        self,
        account_identifier: str,
        auth_payload: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AccountVerificationResult:
        if account_identifier.startswith("invalid"):
            return AccountVerificationResult(
                is_valid=False,
                account_identifier=account_identifier,
                in_game_name="",
                error_message="External PUUID not found on Riot server",
            )
        return AccountVerificationResult(
            is_valid=True,
            account_identifier=account_identifier,
            in_game_name="Valkyrie",
            tagline="NA1",
            region="na",
            metadata={"puuid": account_identifier, "verified_at": "2026-09-20"},
        )

    async def fetch_profile(
        self,
        account_identifier: str,
        region: str | None = None,
        **kwargs: Any,
    ) -> ProviderProfileData:
        return ProviderProfileData(
            account_identifier=account_identifier,
            in_game_name="Valkyrie",
            tagline="NA1",
            region=region or "na",
            avatar_url="https://cdn.riotgames.com/val/valkyrie.png",
            account_level=128,
            raw_data={"puuid": account_identifier, "level": 128},
        )

    async def fetch_stats(
        self,
        account_identifier: str,
        season: str | None = None,
        game_mode: str | None = None,
        region: str | None = None,
        **kwargs: Any,
    ) -> list[ProviderStatsData]:
        return [
            ProviderStatsData(
                season=season or "Episode 8: Act 3",
                game_mode=game_mode or "competitive",
                rank="Immortal 2",
                rank_tier=25,
                rank_rating=145,
                peak_rank="Radiant",
                matches_played=120,
                wins=72,
                losses=48,
                win_rate=60.0,
                kd_ratio=1.35,
                headshot_percentage=28.5,
                damage_per_round=155.2,
                raw_stats={"kills": 2430, "deaths": 1800},
            )
        ]

    async def sync(
        self,
        game_account: GameAccount,
        **kwargs: Any,
    ) -> ProviderSyncResult:
        if game_account.account_identifier == "sync_fail_id":
            return ProviderSyncResult(
                is_success=False,
                error_message="Riot API timeout during telemetry sync",
            )

        profile = await self.fetch_profile(game_account.account_identifier, region=game_account.region)
        stats = await self.fetch_stats(game_account.account_identifier, region=game_account.region)
        return ProviderSyncResult(
            is_success=True,
            profile=profile,
            stats=stats,
        )


# ==============================================================================
# 1. Abstract Base Class & Adapter Pattern Tests
# ==============================================================================

def test_game_provider_abstract_instantiation_prevented():
    """Verify GameProvider ABC cannot be instantiated directly without concrete methods."""
    with pytest.raises(TypeError) as exc_info:
        GameProvider()  # type: ignore
    assert "Can't instantiate abstract class GameProvider" in str(exc_info.value)


def test_mock_adapter_conforms_to_contract():
    """Verify concrete adapter instantiates and exposes contract properties."""
    adapter = MockRiotAdapter()
    assert adapter.platform_name == "riot"
    assert "Valorant" in adapter.supported_games


# ==============================================================================
# 2. Registry Tests
# ==============================================================================

def test_provider_registry_lifecycle():
    """Verify registration, lookup, case-insensitivity, and listing in GameProviderRegistry."""
    registry = GameProviderRegistry()
    adapter = MockRiotAdapter()

    assert not registry.has_provider("riot")
    assert registry.list_supported_platforms() == []

    # Register
    registry.register("Riot", adapter)
    assert registry.has_provider("riot")
    assert registry.has_provider("RIOT")
    assert registry.get("riot") is adapter
    assert registry.get("RIOT") is adapter
    assert registry.list_supported_platforms() == ["riot"]

    # Unknown provider raises ProviderNotFoundException
    with pytest.raises(ProviderNotFoundException) as exc_info:
        registry.get("steam")
    assert "No game provider registered for platform 'steam'" in str(exc_info.value)

    # Clear
    registry.clear()
    assert not registry.has_provider("riot")


# ==============================================================================
# 3. Schema Validation Tests
# ==============================================================================

def test_game_account_link_request_validation():
    """Verify whitespace stripping and validations on link request schema."""
    req = GameAccountLinkRequest(
        platform="  riot  ",
        game_name="  Valorant  ",
        account_identifier="  puuid-12345  ",
        in_game_name="  Phoenix  ",
        tagline="  EUW  ",
        region="  eu  ",
    )
    assert req.platform == "riot"
    assert req.game_name == "Valorant"
    assert req.account_identifier == "puuid-12345"
    assert req.in_game_name == "Phoenix"
    assert req.tagline == "EUW"
    assert req.region == "eu"


def test_game_account_empty_fields_rejection():
    """Verify empty strings are rejected for mandatory identifiers."""
    with pytest.raises(ValueError):
        GameAccountLinkRequest(
            platform="   ",
            game_name="Valorant",
            account_identifier="id-123",
            in_game_name="Player",
        )


# ==============================================================================
# 4. Domain Service Layer Tests (Mock Repositories)
# ==============================================================================

@pytest.fixture
def mock_db_session() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def test_registry() -> GameProviderRegistry:
    reg = GameProviderRegistry()
    reg.register("riot", MockRiotAdapter())
    return reg


@pytest.mark.asyncio
async def test_game_service_link_account_with_adapter_verification(
    mock_db_session: AsyncMock,
    test_registry: GameProviderRegistry,
):
    """Verify linking an account automatically calls registered adapter for verification."""
    user_id = uuid.uuid4()
    mock_account_repo = AsyncMock()
    mock_stat_repo = AsyncMock()

    # User has not previously linked this account
    mock_account_repo.get_user_account_by_platform.return_value = None
    mock_account_repo.get_primary_account.return_value = None
    mock_account_repo.create.side_effect = lambda acc: acc

    service = GameService(
        db=mock_db_session,
        account_repo=mock_account_repo,
        stat_repo=mock_stat_repo,
        registry=test_registry,
    )

    payload = GameAccountLinkRequest(
        platform="riot",
        game_name="Valorant",
        account_identifier="puuid-valk-999",
        in_game_name="TempHandle",
        is_primary=True,
    )

    account = await service.link_account(user_id=user_id, payload=payload)

    assert account.user_id == user_id
    assert account.platform == "riot"
    assert account.is_verified is True
    assert account.in_game_name == "Valkyrie"  # From adapter verification
    assert account.tagline == "NA1"
    assert account.is_primary is True
    assert mock_account_repo.create.called


@pytest.mark.asyncio
async def test_game_service_link_duplicate_account_conflict(
    mock_db_session: AsyncMock,
    test_registry: GameProviderRegistry,
):
    """Verify attempting to link the same external account raises ConflictException."""
    user_id = uuid.uuid4()
    mock_account_repo = AsyncMock()
    mock_stat_repo = AsyncMock()

    mock_account_repo.get_user_account_by_platform.return_value = GameAccount(
        user_id=user_id,
        platform="riot",
        account_identifier="puuid-valk-999",
        game_name="Valorant",
        in_game_name="Valkyrie",
    )

    service = GameService(
        db=mock_db_session,
        account_repo=mock_account_repo,
        stat_repo=mock_stat_repo,
        registry=test_registry,
    )

    payload = GameAccountLinkRequest(
        platform="riot",
        game_name="Valorant",
        account_identifier="puuid-valk-999",
        in_game_name="Valkyrie",
    )

    with pytest.raises(ConflictException) as exc_info:
        await service.link_account(user_id=user_id, payload=payload)
    assert "already linked" in str(exc_info.value)


@pytest.mark.asyncio
async def test_game_service_sync_account_success(
    mock_db_session: AsyncMock,
    test_registry: GameProviderRegistry,
):
    """Verify sync_account calls adapter, updates account, and upserts player stats."""
    user_id = uuid.uuid4()
    account_id = uuid.uuid4()
    mock_account_repo = AsyncMock()
    mock_stat_repo = AsyncMock()

    existing_account = GameAccount(
        id=account_id,
        user_id=user_id,
        platform="riot",
        game_name="Valorant",
        account_identifier="puuid-valk-123",
        in_game_name="Valkyrie",
        tagline="NA1",
        region="na",
        is_verified=True,
    )
    mock_account_repo.get_by_id.return_value = existing_account
    mock_account_repo.update_sync_data.return_value = existing_account

    upserted_stat = PlayerStat(
        id=uuid.uuid4(),
        game_account_id=account_id,
        user_id=user_id,
        season="Episode 8: Act 3",
        game_mode="competitive",
        rank="Immortal 2",
        win_rate=60.0,
        kd_ratio=1.35,
    )
    mock_stat_repo.upsert_stat.return_value = upserted_stat

    service = GameService(
        db=mock_db_session,
        account_repo=mock_account_repo,
        stat_repo=mock_stat_repo,
        registry=test_registry,
    )

    updated_account, stats, sync_res = await service.sync_account(
        user_id=user_id,
        account_id=account_id,
    )

    assert sync_res.is_success is True
    assert len(stats) == 1
    assert stats[0].rank == "Immortal 2"
    assert mock_account_repo.update_sync_data.called
    assert mock_stat_repo.upsert_stat.called


@pytest.mark.asyncio
async def test_game_service_sync_unregistered_platform_validation_error(
    mock_db_session: AsyncMock,
    test_registry: GameProviderRegistry,
):
    """Verify syncing account on platform without adapter raises ValidationException."""
    user_id = uuid.uuid4()
    account_id = uuid.uuid4()
    mock_account_repo = AsyncMock()
    mock_stat_repo = AsyncMock()

    account = GameAccount(
        id=account_id,
        user_id=user_id,
        platform="nintendo",
        game_name="Smash",
        account_identifier="nnid-123",
        in_game_name="Mario",
    )
    mock_account_repo.get_by_id.return_value = account

    service = GameService(
        db=mock_db_session,
        account_repo=mock_account_repo,
        stat_repo=mock_stat_repo,
        registry=test_registry,
    )

    with pytest.raises(ValidationException) as exc_info:
        await service.sync_account(user_id=user_id, account_id=account_id)
    assert "does not have an active synchronization adapter" in str(exc_info.value)


@pytest.mark.asyncio
async def test_game_service_unlink_account(
    mock_db_session: AsyncMock,
    test_registry: GameProviderRegistry,
):
    """Verify unlinking deletes the account via repository."""
    user_id = uuid.uuid4()
    account_id = uuid.uuid4()
    mock_account_repo = AsyncMock()
    mock_stat_repo = AsyncMock()

    account = GameAccount(
        id=account_id,
        user_id=user_id,
        platform="steam",
        game_name="CS2",
        account_identifier="steam-123",
        in_game_name="S1mple",
    )
    mock_account_repo.get_by_id.return_value = account

    service = GameService(
        db=mock_db_session,
        account_repo=mock_account_repo,
        stat_repo=mock_stat_repo,
        registry=test_registry,
    )

    result = await service.unlink_account(user_id=user_id, account_id=account_id)
    assert result is True
    assert mock_account_repo.delete.called


# ==============================================================================
# 5. API Endpoint Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_game_accounts_unauthenticated(client: AsyncClient):
    """Verify /api/v1/games/accounts endpoints require Bearer authentication."""
    res_list = await client.get("/api/v1/games/accounts")
    assert res_list.status_code == 401

    res_link = await client.post(
        "/api/v1/games/accounts",
        json={
            "platform": "riot",
            "game_name": "Valorant",
            "account_identifier": "id-123",
            "in_game_name": "Handle",
        },
    )
    assert res_link.status_code == 401


@pytest.mark.asyncio
async def test_game_accounts_api_flow(authenticated_client: AsyncClient, mock_user: User):
    """
    Test authenticated API flow:
    - Link account
    - Get user accounts
    - Verify account
    - Sync account
    - Retrieve stats
    - Set primary
    - Unlink account
    """
    from app.core.dependencies import get_game_service
    from app.main import app

    # Create mock game service with mock data
    mock_service = AsyncMock()
    app.dependency_overrides[get_game_service] = lambda: mock_service

    now = datetime.now(timezone.utc)
    acc_id = uuid.uuid4()
    dummy_account = GameAccount(
        id=acc_id,
        user_id=mock_user.id,
        platform="riot",
        game_name="Valorant",
        account_identifier="puuid-api-test",
        in_game_name="Valkyrie",
        tagline="NA1",
        region="na",
        is_verified=True,
        is_primary=True,
        created_at=now,
        updated_at=now,
    )

    mock_service.link_account.return_value = dummy_account
    mock_service.get_user_accounts.return_value = [dummy_account]
    mock_service.get_account_by_id.return_value = dummy_account
    mock_service.verify_account.return_value = dummy_account

    sync_stat = PlayerStat(
        id=uuid.uuid4(),
        game_account_id=acc_id,
        user_id=mock_user.id,
        season="Episode 8",
        game_mode="competitive",
        rank="Immortal 3",
        win_rate=65.2,
        matches_played=80,
        wins=52,
        losses=28,
        created_at=now,
        updated_at=now,
    )
    sync_dto = ProviderSyncResult(is_success=True, synced_at=now)
    mock_service.sync_account.return_value = (dummy_account, [sync_stat], sync_dto)
    mock_service.get_account_stats.return_value = [sync_stat]
    mock_service.set_primary_account.return_value = dummy_account
    mock_service.unlink_account.return_value = True

    try:
        # 1. Link Account
        res = await authenticated_client.post(
            "/api/v1/games/accounts",
            json={
                "platform": "riot",
                "game_name": "Valorant",
                "account_identifier": "puuid-api-test",
                "in_game_name": "Valkyrie",
                "tagline": "NA1",
                "region": "na",
                "is_primary": True,
            },
        )
        assert res.status_code == 201
        json_data = res.json()
        assert json_data["success"] is True
        assert json_data["data"]["in_game_name"] == "Valkyrie"

        # 2. List Accounts
        res = await authenticated_client.get("/api/v1/games/accounts")
        assert res.status_code == 200
        json_data = res.json()
        assert len(json_data["data"]) == 1

        # 3. Verify Account
        res = await authenticated_client.post(f"/api/v1/games/accounts/{acc_id}/verify")
        assert res.status_code == 200

        # 4. Sync Account
        res = await authenticated_client.post(f"/api/v1/games/accounts/{acc_id}/sync")
        assert res.status_code == 200
        sync_json = res.json()
        assert sync_json["data"]["stats_synced_count"] == 1
        assert sync_json["data"]["latest_rank"] == "Immortal 3"

        # 5. Get Stats
        res = await authenticated_client.get(f"/api/v1/games/accounts/{acc_id}/stats")
        assert res.status_code == 200
        stats_json = res.json()
        assert len(stats_json["data"]) == 1
        assert stats_json["data"][0]["game_mode"] == "competitive"

        # 6. Set Primary
        res = await authenticated_client.put(f"/api/v1/games/accounts/{acc_id}/primary")
        assert res.status_code == 200

        # 7. Unlink
        res = await authenticated_client.delete(f"/api/v1/games/accounts/{acc_id}")
        assert res.status_code == 200
        assert res.json()["data"]["unlinked"] is True

    finally:
        app.dependency_overrides.pop(get_game_service, None)
