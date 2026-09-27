"""
Tests for Steam Authentication and Dota 2 OpenDota Integration:
- Steam OpenID URL construction and claim parsing
- SteamID64 to 32-bit Dota 2 Account ID conversion
- Rank tier medal formatting (Herald to Immortal)
- OpenDotaProvider telemetry normalization (MMR, W/L, Favorite Heroes, Recent Matches)
- Raw API response storage inside JSONB payloads
- Dota2Service linking, real-time sync, and background task scheduling
- API endpoints testing (/games/steam/login, /games/steam/callback, /games/dota2/sync, /games/dota2/me)
"""

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
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
from app.providers.opendota_provider import (
    OpenDotaProvider,
    dota_id_to_steam_id64,
    format_rank_tier,
    steam_id64_to_dota_id,
)
from app.providers.steam_provider import SteamProvider
from app.schemas.dota2 import Dota2SyncResponse
from app.services.dota2_service import Dota2Service, run_background_dota2_sync


# ==============================================================================
# 1. Steam ID & OpenID Claim Parsing Tests
# ==============================================================================

def test_extract_steam_id():
    """Verify extraction of 64-bit Steam ID from OpenID URLs and raw strings."""
    url = "https://steamcommunity.com/openid/id/76561198034567890"
    assert SteamProvider.extract_steam_id(url) == "76561198034567890"

    http_url = "http://steamcommunity.com/openid/id/76561198034567890/"
    assert SteamProvider.extract_steam_id(http_url) == "76561198034567890"

    raw_id = "76561198034567890"
    assert SteamProvider.extract_steam_id(raw_id) == "76561198034567890"

    invalid = "https://evil.com/id/12345"
    assert SteamProvider.extract_steam_id(invalid) is None


# ==============================================================================
# 2. Dota 2 ID Conversion & Rank Tier Tests
# ==============================================================================

def test_dota_id_conversions():
    """Verify 64-bit Steam ID to 32-bit Dota ID arithmetic and reverse conversion."""
    steam_id_64 = "76561198028745818"
    dota_id = steam_id64_to_dota_id(steam_id_64)
    assert dota_id == 68480090
    assert dota_id_to_steam_id64(dota_id) == steam_id_64


def test_format_rank_tier():
    """Verify conversion of OpenDota rank_tier integers to medal names and stars."""
    assert format_rank_tier(None) == "Unranked"
    assert format_rank_tier(0) == "Unranked"
    assert format_rank_tier(11) == "Herald 1"
    assert format_rank_tier(45) == "Archon 5"
    assert format_rank_tier(73) == "Divine 3"
    assert format_rank_tier(80) == "Immortal"
    assert format_rank_tier(80, leaderboard_rank=142) == "Immortal #142"


# ==============================================================================
# 3. OpenDotaProvider Normalization & Raw Storage Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_opendota_provider_fetch_stats_normalization():
    """Verify OpenDotaProvider normalizes MMR, W/L, favorite heroes, and recent matches."""
    provider = OpenDotaProvider()

    # Mock HTTP client responses
    mock_client = AsyncMock()

    player_resp = MagicMock()
    player_resp.status_code = 200
    player_resp.json.return_value = {
        "profile": {"personaname": "Miracle-", "avatarfull": "https://cdn.dota.com/miracle.png"},
        "rank_tier": 80,
        "leaderboard_rank": 15,
        "mmr_estimate": {"estimate": 8500},
    }

    wl_resp = MagicMock()
    wl_resp.status_code = 200
    wl_resp.json.return_value = {"win": 2100, "lose": 1400}

    heroes_resp = MagicMock()
    heroes_resp.status_code = 200
    heroes_resp.json.return_value = [
        {"hero_id": "74", "games": 450, "win": 290},
        {"hero_id": "1", "games": 320, "win": 200},
    ]

    matches_resp = MagicMock()
    matches_resp.status_code = 200
    matches_resp.json.return_value = [
        {
            "match_id": 7891234567,
            "hero_id": 74,
            "kills": 14,
            "deaths": 2,
            "assists": 10,
            "duration": 2100,
            "radiant_win": True,
            "player_slot": 0,
        }
    ]

    mock_client.get.side_effect = [player_resp, wl_resp, heroes_resp, matches_resp]
    provider._client = mock_client

    stats = await provider.fetch_stats("76561198028745818")
    assert len(stats) == 1
    stat = stats[0]

    assert stat.rank == "Immortal #15"
    assert stat.rank_rating == 8500
    assert stat.matches_played == 3500
    assert stat.wins == 2100
    assert stat.losses == 1400
    assert stat.win_rate == 60.0

    raw = stat.raw_stats
    assert raw["player_name"] == "Miracle-"
    assert raw["mmr"] == 8500
    assert len(raw["favorite_heroes"]) == 2
    assert raw["favorite_heroes"][0]["hero_name"] == "Invoker"
    assert raw["favorite_heroes"][0]["games"] == 450
    assert len(raw["recent_matches"]) == 1
    assert raw["recent_matches"][0]["hero_name"] == "Invoker"
    assert raw["recent_matches"][0]["won"] is True
    assert raw["recent_matches"][0]["kda"] == 12.0
    assert "raw_player_api" in raw
    assert "raw_wl_api" in raw


# ==============================================================================
# 4. Dota2Service Domain Logic Tests
# ==============================================================================

def test_get_steam_login_url():
    """Verify Steam OpenID login URL is constructed with correct OpenID 2.0 parameters."""
    mock_db = AsyncMock()
    service = Dota2Service(mock_db)

    res = service.get_steam_login_url(return_to="http://localhost:3000/callback")
    assert "https://steamcommunity.com/openid/login" in res.login_url
    assert "openid.mode=checkid_setup" in res.login_url
    assert "return_to=http%3A%2F%2Flocalhost%3A3000%2Fcallback" in res.login_url
    assert res.return_to == "http://localhost:3000/callback"


@pytest.mark.asyncio
async def test_verify_and_link_steam():
    """Verify OpenID callback verifies ownership and creates verified GameAccount."""
    mock_db = AsyncMock()
    mock_account_repo = AsyncMock()
    mock_stat_repo = AsyncMock()
    mock_steam_provider = AsyncMock()

    user_id = uuid.uuid4()
    steam_id = "76561198028745818"

    mock_steam_provider.verify_account.return_value = AccountVerificationResult(
        is_valid=True,
        account_identifier=steam_id,
        in_game_name="Valkyrie",
        region="us",
        metadata={"steam_id": steam_id, "avatar_url": "https://avatar.png"},
    )
    mock_account_repo.get_user_account_by_platform.return_value = None
    mock_account_repo.create.side_effect = lambda acc: acc

    service = Dota2Service(
        db=mock_db,
        account_repo=mock_account_repo,
        stat_repo=mock_stat_repo,
        steam_provider=mock_steam_provider,
    )

    openid_params = {
        "openid.claimed_id": f"https://steamcommunity.com/openid/id/{steam_id}",
        "openid.sig": "signature_abc",
    }

    account = await service.verify_and_link_steam(user_id=user_id, openid_params=openid_params)

    assert account.user_id == user_id
    assert account.game_name == "Dota 2"
    assert account.platform == "steam"
    assert account.account_identifier == steam_id
    assert account.in_game_name == "Valkyrie"
    assert account.is_verified is True
    assert mock_account_repo.create.called


@pytest.mark.asyncio
async def test_sync_dota2_account_persists_raw_and_stats():
    """Verify sync_dota2_account updates GameAccount raw JSONB and upserts PlayerStat."""
    mock_db = AsyncMock()
    mock_account_repo = AsyncMock()
    mock_stat_repo = AsyncMock()
    mock_opendota_provider = AsyncMock()

    user_id = uuid.uuid4()
    acc_id = uuid.uuid4()
    steam_id = "76561198028745818"

    existing_account = GameAccount(
        id=acc_id,
        user_id=user_id,
        platform="steam",
        game_name="Dota 2",
        account_identifier=steam_id,
        in_game_name="OldHandle",
        is_verified=True,
    )
    mock_account_repo.get_by_id.return_value = existing_account
    mock_account_repo.update.return_value = existing_account

    telemetry = {
        "steam_id": steam_id,
        "dota_account_id": 68480090,
        "player_name": "NewHandle",
        "avatar": "https://cdn.dota.com/avatar.png",
        "mmr": 5120,
        "rank": "Divine 4",
        "rank_tier": 74,
        "wins": 1500,
        "losses": 1100,
        "win_rate": 57.69,
        "favorite_heroes": [
            {"hero_id": 1, "hero_name": "Anti-Mage", "games": 200, "wins": 130, "win_rate": 65.0}
        ],
        "recent_matches": [
            {
                "match_id": 123456,
                "hero_id": 1,
                "hero_name": "Anti-Mage",
                "kills": 10,
                "deaths": 1,
                "assists": 8,
                "kda": 18.0,
                "won": True,
                "duration_minutes": 35.5,
            }
        ],
    }

    stat_dto = ProviderStatsData(
        season="Current",
        game_mode="ranked",
        rank="Divine 4",
        rank_tier=74,
        rank_rating=5120,
        matches_played=2600,
        wins=1500,
        losses=1100,
        win_rate=57.69,
        kd_ratio=2.4,
        raw_stats=telemetry,
    )

    mock_opendota_provider.sync.return_value = ProviderSyncResult(
        is_success=True,
        profile=ProviderProfileData(
            account_identifier=steam_id,
            in_game_name="NewHandle",
            avatar_url="https://cdn.dota.com/avatar.png",
        ),
        stats=[stat_dto],
    )

    service = Dota2Service(
        db=mock_db,
        account_repo=mock_account_repo,
        stat_repo=mock_stat_repo,
        opendota_provider=mock_opendota_provider,
    )

    result: Dota2SyncResponse = await service.sync_dota2_account(
        user_id=user_id,
        account_id=acc_id,
    )

    assert result.player_name == "NewHandle"
    assert result.mmr == 5120
    assert result.rank == "Divine 4"
    assert result.wins == 1500
    assert len(result.favorite_heroes) == 1
    assert result.favorite_heroes[0].hero_name == "Anti-Mage"
    assert len(result.recent_matches) == 1
    assert result.recent_matches[0].won is True
    assert mock_account_repo.update.called
    assert mock_stat_repo.upsert_stat.called


# ==============================================================================
# 5. API Endpoints & Swagger Verification
# ==============================================================================

@pytest.mark.asyncio
async def test_steam_login_url_endpoint(client: AsyncClient):
    """Verify GET /api/v1/games/steam/login returns OpenID login URL."""
    res = await client.get("/api/v1/games/steam/login")
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["success"] is True
    assert "https://steamcommunity.com/openid/login" in json_data["data"]["login_url"]


@pytest.mark.asyncio
async def test_dota2_sync_endpoint(authenticated_client: AsyncClient, mock_user: User):
    """Verify POST /api/v1/games/dota2/sync endpoint triggers telemetry refresh."""
    from app.core.dependencies import get_dota2_service
    from app.main import app

    mock_dota_service = AsyncMock()
    app.dependency_overrides[get_dota2_service] = lambda: mock_dota_service

    now = datetime.now(timezone.utc)
    acc_id = uuid.uuid4()
    mock_sync_response = Dota2SyncResponse(
        account_id=acc_id,
        user_id=mock_user.id,
        steam_id="76561198028745818",
        player_name="DotaPro",
        avatar="https://avatar.png",
        mmr=6200,
        rank="Immortal",
        wins=1800,
        losses=1200,
        favorite_heroes=[],
        recent_matches=[],
        is_verified=True,
        last_synced_at=now,
        sync_mode="realtime",
        raw_profile_data={"mmr": 6200},
    )
    mock_dota_service.sync_dota2_account.return_value = mock_sync_response

    try:
        res = await authenticated_client.post("/api/v1/games/dota2/sync")
        assert res.status_code == 200
        json_data = res.json()
        assert json_data["success"] is True
        assert json_data["data"]["player_name"] == "DotaPro"
        assert json_data["data"]["mmr"] == 6200
    finally:
        app.dependency_overrides.pop(get_dota2_service, None)


@pytest.mark.asyncio
async def test_dota2_sync_background_endpoint(authenticated_client: AsyncClient, mock_user: User):
    """Verify POST /api/v1/games/dota2/sync?background=true dispatches background task."""
    from app.core.dependencies import get_dota2_service
    from app.main import app

    mock_dota_service = AsyncMock()
    app.dependency_overrides[get_dota2_service] = lambda: mock_dota_service

    acc_id = uuid.uuid4()
    mock_account = GameAccount(
        id=acc_id,
        user_id=mock_user.id,
        platform="steam",
        game_name="Dota 2",
        account_identifier="76561198028745818",
        in_game_name="DotaPro",
        is_verified=True,
    )
    mock_dota_service.get_or_create_dota_account.return_value = mock_account

    try:
        res = await authenticated_client.post(
            "/api/v1/games/dota2/sync?background=true&steam_id=76561198028745818"
        )
        assert res.status_code == 200
        json_data = res.json()
        assert json_data["success"] is True
        assert json_data["data"]["sync_mode"] == "background"
    finally:
        app.dependency_overrides.pop(get_dota2_service, None)


@pytest.mark.asyncio
async def test_dota2_get_me_endpoint(authenticated_client: AsyncClient, mock_user: User):
    """Verify GET /api/v1/games/dota2/me returns cached competitive Dota 2 profile."""
    from app.core.dependencies import get_dota2_service
    from app.main import app

    mock_dota_service = AsyncMock()
    app.dependency_overrides[get_dota2_service] = lambda: mock_dota_service

    acc_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_dota_service.get_dota2_profile.return_value = Dota2SyncResponse(
        account_id=acc_id,
        user_id=mock_user.id,
        steam_id="76561198028745818",
        player_name="Valkyrie",
        avatar=None,
        mmr=5400,
        rank="Divine 5",
        wins=1200,
        losses=900,
        favorite_heroes=[],
        recent_matches=[],
        is_verified=True,
        last_synced_at=now,
        sync_mode="cached",
    )

    try:
        res = await authenticated_client.get("/api/v1/games/dota2/me")
        assert res.status_code == 200
        json_data = res.json()
        assert json_data["success"] is True
        assert json_data["data"]["rank"] == "Divine 5"
    finally:
        app.dependency_overrides.pop(get_dota2_service, None)
