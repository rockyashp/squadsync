"""
Unit tests for OpenDotaProvider.
Tests SteamID64 to 32-bit conversion, rank tier medal mapping,
OpenDota API calls, rate limit handling, telemetry parsing, and DTO conversion.
"""

from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import pytest

from app.models.game_account import GameAccount
from app.providers.dto import (
    AccountVerificationResult,
    ProviderProfileData,
    ProviderSyncResult,
)
from app.providers.exceptions import (
    ProviderAPIException,
    ProviderRateLimitException,
)
from app.providers.opendota_provider import (
    OpenDotaProvider,
    dota_id_to_steam_id64,
    format_rank_tier,
    steam_id64_to_dota_id,
)


def test_dota_id_conversions():
    """Test steam_id64_to_dota_id and dota_id_to_steam_id64."""
    steam_id = "76561198012345678"
    dota_id = steam_id64_to_dota_id(steam_id)
    assert dota_id > 0
    assert dota_id_to_steam_id64(dota_id) == steam_id

    # Fallback / edge cases
    assert steam_id64_to_dota_id("not_a_number") == 0
    assert steam_id64_to_dota_id(12345) == 12345


def test_format_rank_tier():
    """Test format_rank_tier mapping logic."""
    assert format_rank_tier(None) == "Unranked"
    assert format_rank_tier(0) == "Unranked"
    assert format_rank_tier(11) == "Herald 1"
    assert format_rank_tier(45) == "Archon 5"
    assert format_rank_tier(73) == "Divine 3"
    assert format_rank_tier(80) == "Immortal"
    assert format_rank_tier(80, leaderboard_rank=142) == "Immortal #142"
    assert format_rank_tier(90) == "Unranked"


@pytest.mark.asyncio
async def test_opendota_verify_account_invalid_id():
    """Test verify_account returns invalid when ID cannot be converted."""
    provider = OpenDotaProvider()
    result = await provider.verify_account("invalid_id")
    assert not result.is_valid
    assert "Invalid Steam ID or Dota 2 Account ID" in result.error_message


@pytest.mark.asyncio
async def test_opendota_verify_account_success():
    """Test verify_account succeeds with valid profile."""
    provider = OpenDotaProvider()
    with patch.object(
        provider,
        "fetch_profile",
        new=AsyncMock(
            return_value=ProviderProfileData(
                account_identifier="76561198012345678",
                in_game_name="Miracle-",
                avatar_url="https://opendota.com/avatar.jpg",
                region="JO",
                raw_data={"profile": {"account_id": 52079950}},
            )
        ),
    ):
        result = await provider.verify_account("76561198012345678")

    assert result.is_valid
    assert result.in_game_name == "Miracle-"
    assert result.region == "JO"
    assert "dota_account_id" in result.metadata


@pytest.mark.asyncio
async def test_opendota_verify_account_exception():
    """Test verify_account handles exception gracefully."""
    provider = OpenDotaProvider()
    with patch.object(
        provider,
        "fetch_profile",
        new=AsyncMock(side_effect=Exception("API connection failure")),
    ):
        result = await provider.verify_account("76561198012345678")

    assert not result.is_valid
    assert "API connection failure" in result.error_message


@pytest.mark.asyncio
async def test_opendota_fetch_profile_rate_limited():
    """Test fetch_profile raises ProviderRateLimitException on HTTP 429."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_res = AsyncMock()
    mock_res.status_code = 429
    mock_client.get.return_value = mock_res

    provider = OpenDotaProvider(http_client=mock_client)
    with pytest.raises(ProviderRateLimitException, match="rate limit"):
        await provider.fetch_profile("76561198012345678")


@pytest.mark.asyncio
async def test_opendota_fetch_profile_api_error():
    """Test fetch_profile raises ProviderAPIException on non-200 HTTP status."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_res = AsyncMock()
    mock_res.status_code = 502
    mock_client.get.return_value = mock_res

    provider = OpenDotaProvider(http_client=mock_client)
    with pytest.raises(ProviderAPIException, match="OpenDota API error: HTTP 502"):
        await provider.fetch_profile("76561198012345678")


@pytest.mark.asyncio
async def test_opendota_fetch_profile_network_error():
    """Test fetch_profile raises ProviderAPIException on network request failure."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.side_effect = httpx.RequestError("Read timeout")

    provider = OpenDotaProvider(http_client=mock_client)
    with pytest.raises(ProviderAPIException, match="OpenDota network error"):
        await provider.fetch_profile("76561198012345678")


@pytest.mark.asyncio
async def test_opendota_fetch_stats_comprehensive():
    """Test fetch_stats processes matches, heroes, win/loss, and computes metrics."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    # Responses for the 4 calls: player overview, wl, heroes, recentMatches
    player_res = AsyncMock(status_code=200)
    player_res.json = MagicMock(return_value={
        "profile": {"personaname": "Topson", "avatarfull": "https://avatar.png"},
        "rank_tier": 80,
        "leaderboard_rank": 5,
        "mmr_estimate": {"estimate": 11200},
    })

    wl_res = AsyncMock(status_code=200)
    wl_res.json = MagicMock(return_value={"win": 4500, "lose": 2500})

    heroes_res = AsyncMock(status_code=200)
    heroes_res.json = MagicMock(return_value=[
        {"hero_id": 1, "games": 200, "win": 130},
        {"hero_id": 2, "games": 100, "win": 60},
    ])

    matches_res = AsyncMock(status_code=200)
    matches_res.json = MagicMock(return_value=[
        {
            "match_id": 7000000001,
            "hero_id": 1,
            "kills": 15,
            "deaths": 2,
            "assists": 10,
            "player_slot": 0,  # radiant
            "radiant_win": True,
            "duration": 2400,
            "start_time": 1700000000,
        },
        {
            "match_id": 7000000002,
            "hero_id": 2,
            "kills": 5,
            "deaths": 8,
            "assists": 6,
            "player_slot": 130,  # dire
            "radiant_win": True,  # dire lost
            "duration": 1800,
            "start_time": 1700003000,
        },
    ])

    mock_client.get.side_effect = [player_res, wl_res, heroes_res, matches_res]

    provider = OpenDotaProvider(api_key="TEST_KEY", http_client=mock_client)
    stats_list = await provider.fetch_stats("76561198012345678")

    assert len(stats_list) == 1
    stat = stats_list[0]
    assert stat.rank == "Immortal #5"
    assert stat.rank_rating == 11200
    assert stat.matches_played == 7000
    assert stat.wins == 4500
    assert stat.losses == 2500
    assert stat.win_rate == round((4500 / 7000 * 100), 2)
    assert stat.kd_ratio is not None
    assert len(stat.raw_stats["favorite_heroes"]) == 2
    assert len(stat.raw_stats["recent_matches"]) == 2
    assert stat.raw_stats["recent_matches"][0]["won"] is True
    assert stat.raw_stats["recent_matches"][1]["won"] is False


@pytest.mark.asyncio
async def test_opendota_sync_failure():
    """Test OpenDota sync handles errors and returns failure result."""
    provider = OpenDotaProvider()
    account = GameAccount(
        account_identifier="76561198012345678",
        region="EU",
        platform="opendota",
        game_name="Dota 2",
    )

    with patch.object(
        provider,
        "fetch_profile",
        new=AsyncMock(side_effect=Exception("OpenDota backend unavailable")),
    ):
        result = await provider.sync(account)
        assert not result.is_success
        assert "OpenDota backend unavailable" in result.error_message
