"""
Unit tests for SteamProvider.
Tests Steam OpenID 2.0 parsing, cryptographic assertion verification,
profile retrieval, and standardized DTO transformations with HTTP mocking.
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
    ProviderException,
)
from app.providers.steam_provider import SteamProvider


@pytest.mark.asyncio
async def test_steam_provider_extract_steam_id():
    """Test Steam ID extraction from OpenID claimed_id URLs and raw 64-bit strings."""
    # Valid OpenID claimed_id URL
    url = "https://steamcommunity.com/openid/id/76561198012345678"
    assert SteamProvider.extract_steam_id(url) == "76561198012345678"

    # Valid HTTP claimed_id URL
    http_url = "http://steamcommunity.com/openid/id/76561198012345678/"
    assert SteamProvider.extract_steam_id(http_url) == "76561198012345678"

    # Raw valid SteamID64
    raw_id = "76561198012345678"
    assert SteamProvider.extract_steam_id(raw_id) == "76561198012345678"

    # Invalid URLs/strings
    assert SteamProvider.extract_steam_id("https://steamcommunity.com/id/customurl") is None
    assert SteamProvider.extract_steam_id("12345") is None
    assert SteamProvider.extract_steam_id("") is None


@pytest.mark.asyncio
async def test_steam_provider_verify_invalid_steam_id():
    """Test verify_account returns invalid result when SteamID format is invalid."""
    provider = SteamProvider()
    result = await provider.verify_account("invalid_id")
    assert not result.is_valid
    assert "Invalid SteamID64 format" in result.error_message


@pytest.mark.asyncio
async def test_steam_provider_verify_openid_success():
    """Test verify_account successfully validates OpenID assertion."""
    valid_steam_id = "76561198012345678"
    claimed_id = f"https://steamcommunity.com/openid/id/{valid_steam_id}"
    auth_payload = {
        "openid.sig": "test_signature",
        "openid.claimed_id": claimed_id,
    }

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.text = "ns:http://specs.openid.net/auth/2.0\nis_valid:true\n"
    mock_client.post.return_value = mock_response

    provider = SteamProvider(http_client=mock_client)

    with patch.object(
        provider,
        "fetch_profile",
        new=AsyncMock(
            return_value=ProviderProfileData(
                account_identifier=valid_steam_id,
                in_game_name="GabeNewell",
                avatar_url="https://steamcdn.com/avatar.jpg",
                region="US",
                raw_data={"personaname": "GabeNewell"},
            )
        ),
    ):
        result = await provider.verify_account(valid_steam_id, auth_payload=auth_payload)

    assert result.is_valid
    assert result.account_identifier == valid_steam_id
    assert result.in_game_name == "GabeNewell"
    assert result.region == "US"
    assert result.metadata["steam_id"] == valid_steam_id


@pytest.mark.asyncio
async def test_steam_provider_verify_openid_server_error():
    """Test verify_account handles HTTP error from Steam OpenID server."""
    valid_steam_id = "76561198012345678"
    auth_payload = {"openid.sig": "test_sig"}

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = AsyncMock()
    mock_response.status_code = 500
    mock_client.post.return_value = mock_response

    provider = SteamProvider(http_client=mock_client)
    result = await provider.verify_account(valid_steam_id, auth_payload=auth_payload)

    assert not result.is_valid
    assert "Steam OpenID verification server returned HTTP 500" in result.error_message


@pytest.mark.asyncio
async def test_steam_provider_verify_openid_signature_invalid():
    """Test verify_account handles is_valid:false from Valve."""
    valid_steam_id = "76561198012345678"
    auth_payload = {"openid.sig": "bad_sig"}

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.text = "ns:http://specs.openid.net/auth/2.0\nis_valid:false\n"
    mock_client.post.return_value = mock_response

    provider = SteamProvider(http_client=mock_client)
    result = await provider.verify_account(valid_steam_id, auth_payload=auth_payload)

    assert not result.is_valid
    assert "Steam OpenID signature verification failed" in result.error_message


@pytest.mark.asyncio
async def test_steam_provider_verify_openid_mismatched_id():
    """Test verify_account when claimed ID doesn't match requested ID."""
    valid_steam_id = "76561198012345678"
    other_steam_id = "76561198999999999"
    auth_payload = {
        "openid.sig": "sig",
        "openid.claimed_id": f"https://steamcommunity.com/openid/id/{other_steam_id}",
    }

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.text = "is_valid:true\n"
    mock_client.post.return_value = mock_response

    provider = SteamProvider(http_client=mock_client)
    result = await provider.verify_account(valid_steam_id, auth_payload=auth_payload)

    assert not result.is_valid
    assert "does not match requested SteamID" in result.error_message


@pytest.mark.asyncio
async def test_steam_provider_verify_network_error():
    """Test verify_account handles network communication error gracefully."""
    valid_steam_id = "76561198012345678"
    auth_payload = {"openid.sig": "sig"}

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.side_effect = httpx.RequestError("Connection timed out")

    provider = SteamProvider(http_client=mock_client)
    result = await provider.verify_account(valid_steam_id, auth_payload=auth_payload)

    assert not result.is_valid
    assert "Failed to communicate with Steam OpenID server" in result.error_message


@pytest.mark.asyncio
async def test_steam_provider_verify_profile_fetch_fallback():
    """Test verify_account falls back gracefully when fetch_profile fails."""
    valid_steam_id = "76561198012345678"
    provider = SteamProvider()

    with patch.object(
        provider,
        "fetch_profile",
        new=AsyncMock(side_effect=Exception("Profile fetch error")),
    ):
        result = await provider.verify_account(valid_steam_id)

    assert result.is_valid
    assert result.in_game_name == f"SteamUser_{valid_steam_id[-4:]}"


@pytest.mark.asyncio
async def test_steam_provider_fetch_profile_no_api_key():
    """Test fetch_profile when api_key is None returns fallback data."""
    valid_steam_id = "76561198012345678"
    provider = SteamProvider(api_key="")
    profile = await provider.fetch_profile(valid_steam_id, region="US")

    assert profile.account_identifier == valid_steam_id
    assert profile.in_game_name == f"SteamUser_{valid_steam_id[-4:]}"
    assert profile.region == "US"
    assert profile.avatar_url is not None


@pytest.mark.asyncio
async def test_steam_provider_fetch_profile_success():
    """Test fetch_profile with configured API key parses Steam Web API response."""
    valid_steam_id = "76561198012345678"
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = MagicMock(return_value={
        "response": {
            "players": [
                {
                    "steamid": valid_steam_id,
                    "personaname": "Dendi",
                    "avatarfull": "https://avatars.steamstatic.com/dendi.jpg",
                    "loccountrycode": "UA",
                }
            ]
        }
    })
    mock_client.get.return_value = mock_response

    provider = SteamProvider(api_key="TEST_API_KEY", http_client=mock_client)
    profile = await provider.fetch_profile(valid_steam_id)

    assert profile.account_identifier == valid_steam_id
    assert profile.in_game_name == "Dendi"
    assert profile.region == "UA"
    assert profile.avatar_url == "https://avatars.steamstatic.com/dendi.jpg"


@pytest.mark.asyncio
async def test_steam_provider_fetch_profile_api_errors():
    """Test fetch_profile error branches: non-200 status, empty players, network error."""
    valid_steam_id = "76561198012345678"
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    # 1. Non-200 response
    mock_res_500 = AsyncMock()
    mock_res_500.status_code = 503
    mock_client.get.return_value = mock_res_500

    provider = SteamProvider(api_key="TEST_API_KEY", http_client=mock_client)
    with pytest.raises(ProviderAPIException, match="Steam Web API error: HTTP 503"):
        await provider.fetch_profile(valid_steam_id)

    # 2. Empty players list
    mock_res_empty = AsyncMock()
    mock_res_empty.status_code = 200
    mock_res_empty.json = MagicMock(return_value={"response": {"players": []}})
    mock_client.get.return_value = mock_res_empty

    with pytest.raises(ProviderException, match="No Steam profile found"):
        await provider.fetch_profile(valid_steam_id)

    # 3. Network RequestError
    mock_client.get.side_effect = httpx.RequestError("Host unreachable")
    with pytest.raises(ProviderAPIException, match="Steam network request failed"):
        await provider.fetch_profile(valid_steam_id)


@pytest.mark.asyncio
async def test_steam_provider_fetch_stats():
    """Test fetch_stats returns empty list for generic Steam platform."""
    provider = SteamProvider()
    stats = await provider.fetch_stats("76561198012345678")
    assert stats == []


@pytest.mark.asyncio
async def test_steam_provider_sync():
    """Test sync succeeds and fails appropriately."""
    provider = SteamProvider()
    account = GameAccount(
        account_identifier="76561198012345678",
        region="NA",
        platform="steam",
        game_name="Dota 2",
    )

    # Success case
    with patch.object(
        provider,
        "fetch_profile",
        new=AsyncMock(
            return_value=ProviderProfileData(
                account_identifier="76561198012345678",
                in_game_name="ProPlayer",
            )
        ),
    ):
        result = await provider.sync(account)
        assert result.is_success
        assert result.profile.in_game_name == "ProPlayer"

    # Failure case
    with patch.object(
        provider,
        "fetch_profile",
        new=AsyncMock(side_effect=Exception("Sync failed")),
    ):
        result = await provider.sync(account)
        assert not result.is_success
        assert "Sync failed" in result.error_message
