"""
Unit tests for RiotProvider.
Tests Riot Sign-On (RSO) authorization URL generation, token exchange,
/userinfo resolution, account verification, official Account-V1 API integration,
and competitive tier formatting.
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
    ProviderAuthException,
)
from app.providers.riot_provider import (
    RiotProvider,
    format_valorant_tier,
)


def test_format_valorant_tier():
    """Test format_valorant_tier mapping."""
    assert format_valorant_tier(None) == "Unranked"
    assert format_valorant_tier(0) == "Unranked"
    assert format_valorant_tier(3) == "Iron 1"
    assert format_valorant_tier(12) == "Gold 1"
    assert format_valorant_tier(24) == "Immortal 1"
    assert format_valorant_tier(27) == "Radiant"
    assert format_valorant_tier(999) == "Unranked"


def test_riot_provider_get_authorization_url():
    """Test OAuth2 authorization URL construction with client_id and state."""
    provider = RiotProvider(
        client_id="custom-client-id",
        redirect_uri="https://app.squadsync.gg/auth/riot/callback",
    )
    url = provider.get_authorization_url(state="custom-state-123")
    assert "client_id=custom-client-id" in url
    assert "state=custom-state-123" in url
    assert "response_type=code" in url


@pytest.mark.asyncio
async def test_riot_provider_exchange_code_fallback():
    """Test exchange_code_for_tokens without credentials returns mock token."""
    provider = RiotProvider(client_id="", client_secret="")
    tokens = await provider.exchange_code_for_tokens("auth_code_xyz")
    assert "access_token" in tokens
    assert "mock_rso" in tokens["access_token"]


@pytest.mark.asyncio
async def test_riot_provider_exchange_code_configured_success():
    """Test exchange_code_for_tokens with configured credentials queries token endpoint."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_res = AsyncMock()
    mock_res.status_code = 200
    mock_res.json = MagicMock(return_value={
        "access_token": "riot_access_token_123",
        "id_token": "riot_id_token_123",
        "expires_in": 3600,
    })
    mock_client.post.return_value = mock_res

    provider = RiotProvider(
        client_id="client_id",
        client_secret="client_secret",
        http_client=mock_client,
    )
    tokens = await provider.exchange_code_for_tokens("real_code")
    assert tokens["access_token"] == "riot_access_token_123"


@pytest.mark.asyncio
async def test_riot_provider_exchange_code_errors():
    """Test exchange_code_for_tokens handles non-200 and network errors."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_res = AsyncMock(status_code=400)
    mock_client.post.return_value = mock_res

    provider = RiotProvider(
        client_id="client_id",
        client_secret="client_secret",
        http_client=mock_client,
    )
    with pytest.raises(ProviderAuthException, match="Failed to exchange RSO code"):
        await provider.exchange_code_for_tokens("bad_code")

    mock_client.post.side_effect = httpx.RequestError("Network drop")
    with pytest.raises(ProviderAPIException, match="RSO token request network error"):
        await provider.exchange_code_for_tokens("any_code")


@pytest.mark.asyncio
async def test_riot_provider_fetch_userinfo_mock_token():
    """Test fetch_userinfo with mock access token parses quickly."""
    provider = RiotProvider()
    userinfo = await provider.fetch_userinfo("mock_rso_access_token_abc")
    assert "sub" in userinfo
    assert "cpid" in userinfo


@pytest.mark.asyncio
async def test_riot_provider_fetch_userinfo_live():
    """Test fetch_userinfo with live token queries /userinfo endpoint."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_res = AsyncMock(status_code=200)
    mock_res.json = MagicMock(return_value={"sub": "real-puuid-999", "cpid": "EUW1"})
    mock_client.get.return_value = mock_res

    provider = RiotProvider(http_client=mock_client)
    userinfo = await provider.fetch_userinfo("real_live_token")
    assert userinfo["sub"] == "real-puuid-999"


@pytest.mark.asyncio
async def test_riot_provider_fetch_userinfo_errors():
    """Test fetch_userinfo handles non-200 and network errors."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_res = AsyncMock(status_code=401)
    mock_client.get.return_value = mock_res

    provider = RiotProvider(http_client=mock_client)
    with pytest.raises(ProviderAuthException, match="Failed to retrieve userinfo"):
        await provider.fetch_userinfo("invalid_token")

    mock_client.get.side_effect = httpx.RequestError("Connection reset")
    with pytest.raises(ProviderAPIException, match="RSO userinfo network error"):
        await provider.fetch_userinfo("any_token")


@pytest.mark.asyncio
async def test_riot_provider_verify_account_with_code():
    """Test verify_account processes authorization code and extracts PUUID."""
    provider = RiotProvider()
    with patch.object(
        provider,
        "exchange_code_for_tokens",
        new=AsyncMock(return_value={"access_token": "mock_rso_token_123"}),
    ), patch.object(
        provider,
        "fetch_userinfo",
        new=AsyncMock(return_value={"sub": "puuid-verified-123"}),
    ):
        result = await provider.verify_account(
            account_identifier="",
            auth_payload={"code": "sample_auth_code"},
        )

    assert result.is_valid
    assert result.account_identifier == "puuid-verified-123"
    assert "puuid" in result.metadata


@pytest.mark.asyncio
async def test_riot_provider_verify_account_with_access_token():
    """Test verify_account processes access token in payload."""
    provider = RiotProvider()
    with patch.object(
        provider,
        "fetch_userinfo",
        new=AsyncMock(return_value={"sub": "puuid-token-456"}),
    ):
        result = await provider.verify_account(
            account_identifier="",
            auth_payload={"access_token": "mock_rso_token_456"},
        )

    assert result.is_valid
    assert result.account_identifier == "puuid-token-456"


@pytest.mark.asyncio
async def test_riot_provider_fetch_profile_with_api_key():
    """Test fetch_profile with configured API key queries Riot Account-V1."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    # 1. 200 Success
    mock_res_200 = AsyncMock(status_code=200)
    mock_res_200.json = MagicMock(return_value={
        "puuid": "test-puuid-123",
        "gameName": "TenZ",
        "tagLine": "001",
    })
    mock_client.get.return_value = mock_res_200

    provider = RiotProvider(api_key="RGAPI-test-key", http_client=mock_client)
    profile = await provider.fetch_profile("test-puuid-123", region="na")

    assert profile.in_game_name == "TenZ"
    assert profile.tagline == "001"

    # 2. Non-200 Status
    mock_res_404 = AsyncMock(status_code=404)
    mock_client.get.return_value = mock_res_404
    profile_404 = await provider.fetch_profile("test-puuid-123", region="eu")
    assert profile_404.tagline == "NA1"

    # 3. RequestError
    mock_client.get.side_effect = httpx.RequestError("API Timeout")
    profile_err = await provider.fetch_profile("test-puuid-123", region="kr")
    assert "error" in profile_err.raw_data


@pytest.mark.asyncio
async def test_riot_provider_sync_failure():
    """Test sync handles exception and returns failure."""
    provider = RiotProvider()
    account = GameAccount(
        account_identifier="test-puuid",
        region="na",
        platform="riot",
        game_name="Valorant",
    )

    with patch.object(
        provider,
        "fetch_profile",
        new=AsyncMock(side_effect=Exception("Riot API down")),
    ):
        result = await provider.sync(account)
        assert not result.is_success
        assert "Riot API down" in result.error_message
