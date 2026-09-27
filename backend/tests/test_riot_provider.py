"""
Tests for Riot Games Provider and Riot Sign-On (RSO) architecture:
- Conformance to GameProvider adapter pattern contract
- Dynamic configuration handling (no hardcoded API keys)
- RSO OAuth2 URL construction and code/token exchange
- Normalization of required fields:
  * PUUID
  * Summoner Name
  * Rank
  * Current Season
  * Preferred Agent
  * Competitive Tier
- Preservation of raw API responses in PostgreSQL JSONB structures
- RiotService domain orchestration and PlayerStat persistence
- API endpoints testing (/games/riot/login, /games/riot/callback, /games/riot/sync, /games/riot/me)
"""

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock
import uuid

from httpx import AsyncClient
import pytest

from app.models.game_account import GameAccount
from app.models.player_stat import PlayerStat
from app.models.user import User
from app.providers.dto import (
    AccountVerificationResult,
    ProviderProfileData,
    ProviderStatsData,
    ProviderSyncResult,
)
from app.providers.riot_provider import (
    RiotProvider,
    format_valorant_tier,
)
from app.schemas.riot import (
    RiotLoginUrlResponse,
    RiotSyncResponse,
)
from app.services.riot_service import RiotService


# ==============================================================================
# 1. Adapter Contract & Tier Formatting Tests
# ==============================================================================

def test_riot_provider_contract():
    """Verify RiotProvider conforms to GameProvider contract and platform specifications."""
    provider = RiotProvider()
    assert provider.platform_name == "riot"
    assert "Valorant" in provider.supported_games
    assert "League of Legends" in provider.supported_games


def test_format_valorant_tier():
    """Verify Valorant competitive tier integers convert to accurate display ranks."""
    assert format_valorant_tier(None) == "Unranked"
    assert format_valorant_tier(0) == "Unranked"
    assert format_valorant_tier(3) == "Iron 1"
    assert format_valorant_tier(14) == "Gold 3"
    assert format_valorant_tier(20) == "Diamond 3"
    assert format_valorant_tier(25) == "Immortal 2"
    assert format_valorant_tier(27) == "Radiant"


# ==============================================================================
# 2. Riot Sign-On (RSO) URL & Code Exchange Tests
# ==============================================================================

def test_rso_authorization_url():
    """Verify RSO authorization URL construction with client_id, scopes, and state."""
    provider = RiotProvider(
        client_id="squadsync_prod_client",
        redirect_uri="https://squadsync.gg/api/v1/games/riot/callback",
    )
    url = provider.get_authorization_url(state="random_csrf_token_123")
    assert "https://auth.riotgames.com/authorize" in url
    assert "client_id=squadsync_prod_client" in url
    assert "scope=openid+cpid" in url or "scope=openid%20cpid" in url
    assert "state=random_csrf_token_123" in url


@pytest.mark.asyncio
async def test_rso_code_exchange_and_userinfo():
    """Verify exchange_code_for_tokens and fetch_userinfo with mock HTTP client."""
    mock_client = AsyncMock()

    token_resp = MagicMock()
    token_resp.status_code = 200
    token_resp.json.return_value = {
        "access_token": "valid_rso_token_xyz",
        "token_type": "Bearer",
        "expires_in": 3600,
    }

    userinfo_resp = MagicMock()
    userinfo_resp.status_code = 200
    userinfo_resp.json.return_value = {
        "sub": "puuid-verified-998877665544",
        "cpid": "NA1",
    }

    mock_client.post.return_value = token_resp
    mock_client.get.return_value = userinfo_resp

    provider = RiotProvider(
        client_id="client_id_123",
        client_secret="secret_abc",
        http_client=mock_client,
    )

    # 1. Exchange code
    tokens = await provider.exchange_code_for_tokens("auth_code_555")
    assert tokens["access_token"] == "valid_rso_token_xyz"

    # 2. Fetch userinfo
    userinfo = await provider.fetch_userinfo("valid_rso_token_xyz")
    assert userinfo["sub"] == "puuid-verified-998877665544"

    # 3. Verify account via RSO code
    verification = await provider.verify_account(
        account_identifier="",
        auth_payload={"code": "auth_code_555"},
    )
    assert verification.is_valid is True
    assert verification.account_identifier == "puuid-verified-998877665544"


# ==============================================================================
# 3. Required Fields Normalization & Raw Storage Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_riot_provider_fetch_stats_normalized_fields():
    """
    Verify fetch_stats extracts and populates all 6 required fields:
    - PUUID
    - Summoner Name
    - Rank
    - Current Season
    - Preferred Agent
    - Competitive Tier
    """
    provider = RiotProvider()
    puuid = "puuid-valk-1234567890-test"

    stats = await provider.fetch_stats(
        account_identifier=puuid,
        season="Episode 8: Act 3",
        competitive_tier=26,  # Immortal 3
        preferred_agent="Reyna",
        summoner_name="Valkyrie#NA1",
        wins=85,
        losses=35,
    )

    assert len(stats) == 1
    stat = stats[0]

    # Model assertions
    assert stat.season == "Episode 8: Act 3"
    assert stat.rank == "Immortal 3"
    assert stat.rank_tier == 26
    assert stat.matches_played == 120
    assert stat.wins == 85
    assert stat.losses == 35
    assert stat.win_rate == 70.83

    # Raw telemetry verification
    raw = stat.raw_stats
    assert raw["puuid"] == puuid
    assert raw["summoner_name"] == "Valkyrie#NA1"
    assert raw["rank"] == "Immortal 3"
    assert raw["current_season"] == "Episode 8: Act 3"
    assert raw["preferred_agent"] == "Reyna"
    assert raw["competitive_tier"] == 26


# ==============================================================================
# 4. RiotService Domain Logic Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_riot_service_handle_rso_callback():
    """Verify handle_rso_callback creates and verifies GameAccount."""
    mock_db = AsyncMock()
    mock_account_repo = AsyncMock()
    mock_stat_repo = AsyncMock()
    mock_riot_provider = AsyncMock()

    user_id = uuid.uuid4()
    puuid = "puuid-rso-user-112233"

    mock_riot_provider.verify_account.return_value = AccountVerificationResult(
        is_valid=True,
        account_identifier=puuid,
        in_game_name="TenZ",
        tagline="NA1",
        region="na",
        metadata={"puuid": puuid, "source": "rso_test"},
    )
    mock_account_repo.get_user_account_by_platform.return_value = None
    mock_account_repo.create.side_effect = lambda acc: acc

    service = RiotService(
        db=mock_db,
        account_repo=mock_account_repo,
        stat_repo=mock_stat_repo,
        riot_provider=mock_riot_provider,
    )

    account = await service.handle_rso_callback(user_id=user_id, code="rso_code_999")

    assert account.user_id == user_id
    assert account.game_name == "Valorant"
    assert account.platform == "riot"
    assert account.account_identifier == puuid
    assert account.in_game_name == "TenZ"
    assert account.tagline == "NA1"
    assert account.is_verified is True
    assert mock_account_repo.create.called


@pytest.mark.asyncio
async def test_riot_service_sync_persists_raw_and_stats():
    """Verify sync_riot_account persists raw JSON in GameAccount and upserts PlayerStat."""
    mock_db = AsyncMock()
    mock_account_repo = AsyncMock()
    mock_stat_repo = AsyncMock()
    mock_riot_provider = AsyncMock()

    user_id = uuid.uuid4()
    acc_id = uuid.uuid4()
    puuid = "puuid-tenz-val-001"

    existing_account = GameAccount(
        id=acc_id,
        user_id=user_id,
        platform="riot",
        game_name="Valorant",
        account_identifier=puuid,
        in_game_name="TenZ",
        tagline="NA1",
        is_verified=True,
    )
    mock_account_repo.get_by_id.return_value = existing_account
    mock_account_repo.update.return_value = existing_account

    telemetry = {
        "puuid": puuid,
        "summoner_name": "TenZ#NA1",
        "rank": "Radiant",
        "current_season": "Episode 8: Act 3",
        "preferred_agent": "Jett",
        "competitive_tier": 27,
        "wins": 150,
        "losses": 50,
        "win_rate": 75.0,
    }

    stat_dto = ProviderStatsData(
        season="Episode 8: Act 3",
        game_mode="competitive",
        rank="Radiant",
        rank_tier=27,
        rank_rating=650,
        matches_played=200,
        wins=150,
        losses=50,
        win_rate=75.0,
        raw_stats=telemetry,
    )

    mock_riot_provider.sync.return_value = ProviderSyncResult(
        is_success=True,
        profile=ProviderProfileData(
            account_identifier=puuid,
            in_game_name="TenZ#NA1",
        ),
        stats=[stat_dto],
    )

    service = RiotService(
        db=mock_db,
        account_repo=mock_account_repo,
        stat_repo=mock_stat_repo,
        riot_provider=mock_riot_provider,
    )

    res: RiotSyncResponse = await service.sync_riot_account(user_id=user_id, account_id=acc_id)

    assert res.puuid == puuid
    assert res.summoner_name == "TenZ#NA1"
    assert res.rank == "Radiant"
    assert res.current_season == "Episode 8: Act 3"
    assert res.preferred_agent == "Jett"
    assert res.competitive_tier == 27
    assert res.wins == 150
    assert res.losses == 50
    assert res.win_rate == 75.0
    assert mock_account_repo.update.called
    assert mock_stat_repo.upsert_stat.called


# ==============================================================================
# 5. API Endpoints Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_riot_login_endpoint(client: AsyncClient):
    """Verify GET /api/v1/games/riot/login returns RSO authorization URL."""
    res = await client.get("/api/v1/games/riot/login")
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["success"] is True
    assert "https://auth.riotgames.com/authorize" in json_data["data"]["auth_url"]


@pytest.mark.asyncio
async def test_riot_sync_endpoint(authenticated_client: AsyncClient, mock_user: User):
    """Verify POST /api/v1/games/riot/sync triggers telemetry synchronization."""
    from app.core.dependencies import get_riot_service
    from app.main import app

    mock_service = AsyncMock()
    app.dependency_overrides[get_riot_service] = lambda: mock_service

    now = datetime.now(timezone.utc)
    acc_id = uuid.uuid4()
    mock_sync_response = RiotSyncResponse(
        account_id=acc_id,
        user_id=mock_user.id,
        puuid="puuid-api-test-123",
        summoner_name="Valkyrie#NA1",
        rank="Immortal 2",
        current_season="Episode 8: Act 3",
        preferred_agent="Omen",
        competitive_tier=25,
        wins=50,
        losses=25,
        win_rate=66.67,
        is_verified=True,
        last_synced_at=now,
        raw_profile_data={"puuid": "puuid-api-test-123"},
    )
    mock_service.sync_riot_account.return_value = mock_sync_response

    try:
        res = await authenticated_client.post("/api/v1/games/riot/sync")
        assert res.status_code == 200
        json_data = res.json()
        assert json_data["success"] is True
        assert json_data["data"]["summoner_name"] == "Valkyrie#NA1"
        assert json_data["data"]["rank"] == "Immortal 2"
        assert json_data["data"]["preferred_agent"] == "Omen"
        assert json_data["data"]["competitive_tier"] == 25
    finally:
        app.dependency_overrides.pop(get_riot_service, None)


@pytest.mark.asyncio
async def test_riot_get_me_endpoint(authenticated_client: AsyncClient, mock_user: User):
    """Verify GET /api/v1/games/riot/me returns cached competitive Riot profile."""
    from app.core.dependencies import get_riot_service
    from app.main import app

    mock_service = AsyncMock()
    app.dependency_overrides[get_riot_service] = lambda: mock_service

    acc_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_service.get_riot_profile.return_value = RiotSyncResponse(
        account_id=acc_id,
        user_id=mock_user.id,
        puuid="puuid-cached-456",
        summoner_name="Shroud#NA1",
        rank="Radiant",
        current_season="Episode 8: Act 3",
        preferred_agent="Sova",
        competitive_tier=27,
        wins=100,
        losses=30,
        win_rate=76.92,
        is_verified=True,
        last_synced_at=now,
    )

    try:
        res = await authenticated_client.get("/api/v1/games/riot/me")
        assert res.status_code == 200
        json_data = res.json()
        assert json_data["success"] is True
        assert json_data["data"]["preferred_agent"] == "Sova"
        assert json_data["data"]["rank"] == "Radiant"
    finally:
        app.dependency_overrides.pop(get_riot_service, None)
