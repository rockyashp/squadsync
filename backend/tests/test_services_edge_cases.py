"""
Unit tests for edge cases across domain services:
- AuthService (refresh tokens, lockout, forgot/reset password, deactivated users)
- GameService (unsupported platform adapters, sync failures, account updates, unlinking)
- Dota2Service (OpenID validation errors, background sync task, cached profile)
- RiotService (callback validation errors, cached profile)
"""

from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from fastapi import HTTPException
import jwt
import pytest

from app.core.exceptions import (
    EntityNotFoundException,
    ValidationException,
)
from app.constants import TokenTypes
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
)
from app.models.game_account import GameAccount
from app.models.user import User
from app.providers.dto import (
    AccountVerificationResult,
    ProviderProfileData,
    ProviderStatsData,
    ProviderSyncResult,
)
from app.providers.registry import GameProviderRegistry
from app.schemas.auth import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserLoginRequest,
)
from app.schemas.game_account import GameAccountUpdateRequest
from app.services.auth_service import AuthService
from app.services.dota2_service import Dota2Service, run_background_dota2_sync
from app.services.game_service import GameService
from app.services.riot_service import RiotService


# =========================================================================
# AuthService Edge Cases
# =========================================================================

@pytest.mark.asyncio
async def test_auth_service_refresh_tokens_errors():
    """Test refresh_tokens error conditions."""
    mock_db = AsyncMock()
    service = AuthService(mock_db)

    # 1. Expired token
    with patch("app.services.auth_service.decode_token", side_effect=jwt.ExpiredSignatureError):
        with pytest.raises(HTTPException) as exc:
            await service.refresh_tokens("expired_token")
        assert exc.value.status_code == 401
        assert "expired" in exc.value.detail

    # 2. Malformed token
    with patch("app.services.auth_service.decode_token", side_effect=jwt.PyJWTError):
        with pytest.raises(HTTPException) as exc:
            await service.refresh_tokens("malformed_token")
        assert exc.value.status_code == 401
        assert "Invalid refresh token" in exc.value.detail

    # 3. Wrong token type (e.g. access token passed to refresh)
    with patch("app.services.auth_service.decode_token", return_value={"type": "access", "sub": str(uuid.uuid4())}):
        with pytest.raises(HTTPException) as exc:
            await service.refresh_tokens("wrong_type_token")
        assert exc.value.status_code == 401
        assert "Invalid token type" in exc.value.detail

    # 4. Missing subject
    with patch("app.services.auth_service.decode_token", return_value={"type": TokenTypes.REFRESH.value}):
        with pytest.raises(HTTPException) as exc:
            await service.refresh_tokens("no_sub_token")
        assert exc.value.status_code == 401
        assert "Token subject missing" in exc.value.detail

    # 5. Malformed UUID subject
    with patch("app.services.auth_service.decode_token", return_value={"type": TokenTypes.REFRESH.value, "sub": "not-a-uuid"}):
        with pytest.raises(HTTPException) as exc:
            await service.refresh_tokens("bad_uuid_token")
        assert exc.value.status_code == 401
        assert "Malformed token subject" in exc.value.detail

    # 6. User not found
    valid_uuid = uuid.uuid4()
    with patch("app.services.auth_service.decode_token", return_value={"type": TokenTypes.REFRESH.value, "sub": str(valid_uuid)}):
        service.user_service.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await service.refresh_tokens("valid_token")
        assert exc.value.status_code == 401
        assert "no longer exists" in exc.value.detail

    # 7. User account is locked
    locked_user = User(id=valid_uuid, username="locked", email="locked@test.com", is_locked=True, is_active=True)
    with patch("app.services.auth_service.decode_token", return_value={"type": TokenTypes.REFRESH.value, "sub": str(valid_uuid)}):
        service.user_service.get_by_id = AsyncMock(return_value=locked_user)
        with pytest.raises(HTTPException) as exc:
            await service.refresh_tokens("valid_token")
        assert exc.value.status_code == 403
        assert "Account is locked" in exc.value.detail

    # 8. User account is deactivated
    inactive_user = User(id=valid_uuid, username="inactive", email="in@test.com", is_locked=False, is_active=False)
    with patch("app.services.auth_service.decode_token", return_value={"type": TokenTypes.REFRESH.value, "sub": str(valid_uuid)}):
        service.user_service.get_by_id = AsyncMock(return_value=inactive_user)
        with pytest.raises(HTTPException) as exc:
            await service.refresh_tokens("valid_token")
        assert exc.value.status_code == 403
        assert "User account is inactive" in exc.value.detail

    # 9. Successful refresh
    active_user = User(id=valid_uuid, username="active", email="act@test.com", is_locked=False, is_active=True)
    with patch("app.services.auth_service.decode_token", return_value={"type": TokenTypes.REFRESH.value, "sub": str(valid_uuid)}):
        service.user_service.get_by_id = AsyncMock(return_value=active_user)
        tokens = await service.refresh_tokens("valid_token")
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None


@pytest.mark.asyncio
async def test_auth_service_reset_password_branches():
    """Test reset_password token validation and execution."""
    mock_db = AsyncMock()
    service = AuthService(mock_db)

    # 1. Expired token
    with patch("app.services.auth_service.decode_token", side_effect=jwt.ExpiredSignatureError):
        with pytest.raises(HTTPException) as exc:
            await service.reset_password(ResetPasswordRequest(token="expired", new_password="Password123!"))
        assert exc.value.status_code == 400
        assert "expired" in exc.value.detail

    # 2. Malformed token
    with patch("app.services.auth_service.decode_token", side_effect=jwt.PyJWTError):
        with pytest.raises(HTTPException) as exc:
            await service.reset_password(ResetPasswordRequest(token="bad", new_password="Password123!"))
        assert exc.value.status_code == 400

    # 3. Wrong token type
    with patch("app.services.auth_service.decode_token", return_value={"type": "refresh", "sub": str(uuid.uuid4())}):
        with pytest.raises(HTTPException) as exc:
            await service.reset_password(ResetPasswordRequest(token="wrong_type", new_password="Password123!"))
        assert exc.value.status_code == 400
        assert "Invalid token type" in exc.value.detail

    # 4. Missing subject
    with patch("app.services.auth_service.decode_token", return_value={"type": TokenTypes.PASSWORD_RESET.value}):
        with pytest.raises(HTTPException) as exc:
            await service.reset_password(ResetPasswordRequest(token="no_sub", new_password="Password123!"))
        assert exc.value.status_code == 400
        assert "Malformed token subject identifier" in exc.value.detail

    # 5. Malformed subject UUID
    with patch("app.services.auth_service.decode_token", return_value={"type": TokenTypes.PASSWORD_RESET.value, "sub": "invalid-uuid"}):
        with pytest.raises(HTTPException) as exc:
            await service.reset_password(ResetPasswordRequest(token="bad_uuid", new_password="Password123!"))
        assert exc.value.status_code == 400
        assert "Malformed token subject UUID" in exc.value.detail

    # 6. User not found
    valid_uuid = uuid.uuid4()
    with patch("app.services.auth_service.decode_token", return_value={"type": TokenTypes.PASSWORD_RESET.value, "sub": str(valid_uuid)}):
        service.user_service.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await service.reset_password(ResetPasswordRequest(token="valid_tok", new_password="Password123!"))
        assert exc.value.status_code == 400
        assert "User account associated with this token was not found" in exc.value.detail

    # 7. Successful reset
    valid_user = User(id=valid_uuid, username="valid", email="val@test.com", is_locked=True, failed_login_attempts=5)
    with patch("app.services.auth_service.decode_token", return_value={"type": TokenTypes.PASSWORD_RESET.value, "sub": str(valid_uuid)}):
        service.user_service.get_by_id = AsyncMock(return_value=valid_user)
        res = await service.reset_password(ResetPasswordRequest(token="valid_tok", new_password="NewSecurePassword123!"))
        assert "Password has been reset successfully" in res.message
        assert valid_user.is_locked is False
        assert valid_user.failed_login_attempts == 0


@pytest.mark.asyncio
async def test_auth_service_forgot_password():
    """Test forgot_password always returns confirmation."""
    mock_db = AsyncMock()
    service = AuthService(mock_db)

    # User exists
    user = User(id=uuid.uuid4(), username="forgot_user", email="forgot@test.com", is_active=True)
    service.user_service.get_by_email = AsyncMock(return_value=user)
    res = await service.forgot_password(ForgotPasswordRequest(email="forgot@test.com"))
    assert "password reset link has been dispatched" in res.message

    # User does not exist (mitigating user enumeration)
    service.user_service.get_by_email = AsyncMock(return_value=None)
    res2 = await service.forgot_password(ForgotPasswordRequest(email="nonexistent@test.com"))
    assert "password reset link has been dispatched" in res2.message


# =========================================================================
# GameService Edge Cases
# =========================================================================

@pytest.mark.asyncio
async def test_game_service_verify_account_unsupported_platform():
    """Test verify_account on GameService raises ValidationException when platform has no adapter."""
    mock_db = AsyncMock()
    mock_registry = GameProviderRegistry()
    service = GameService(mock_db, registry=mock_registry)

    user_id = uuid.uuid4()
    account_id = uuid.uuid4()
    account = GameAccount(
        id=account_id,
        user_id=user_id,
        platform="unsupported_platform",
        account_identifier="12345",
        game_name="Unknown Game",
    )
    service.get_account_by_id = AsyncMock(return_value=account)

    with pytest.raises(ValidationException, match="does not have an active verification adapter"):
        await service.verify_account(user_id, account_id)


@pytest.mark.asyncio
async def test_game_service_verify_account_failed():
    """Test verify_account on GameService raises ValidationException when provider returns invalid."""
    mock_db = AsyncMock()
    mock_registry = GameProviderRegistry()
    mock_provider = AsyncMock()
    mock_provider.platform_name = "test_plat"
    mock_provider.verify_account.return_value = AccountVerificationResult(
        is_valid=False,
        account_identifier="12345",
        in_game_name="",
        error_message="Verification check rejected",
    )
    mock_registry.register("test_plat", mock_provider)

    service = GameService(mock_db, registry=mock_registry)
    user_id = uuid.uuid4()
    account_id = uuid.uuid4()
    account = GameAccount(
        id=account_id,
        user_id=user_id,
        platform="test_plat",
        account_identifier="12345",
        game_name="Test Game",
    )
    service.get_account_by_id = AsyncMock(return_value=account)

    with pytest.raises(ValidationException, match="Verification check rejected"):
        await service.verify_account(user_id, account_id)


@pytest.mark.asyncio
async def test_game_service_sync_account_failures():
    """Test sync_account when platform unsupported or provider returns failure."""
    mock_db = AsyncMock()
    mock_registry = GameProviderRegistry()
    service = GameService(mock_db, registry=mock_registry)

    user_id = uuid.uuid4()
    account_id = uuid.uuid4()
    account = GameAccount(
        id=account_id,
        user_id=user_id,
        platform="unregistered",
        account_identifier="12345",
        game_name="Game X",
    )
    service.get_account_by_id = AsyncMock(return_value=account)

    with pytest.raises(ValidationException, match="does not have an active synchronization adapter"):
        await service.sync_account(user_id, account_id)

    # Provider registered but sync fails
    mock_provider = AsyncMock()
    mock_provider.platform_name = "unregistered"
    mock_provider.sync.return_value = ProviderSyncResult(
        is_success=False,
        error_message="Sync upstream failure",
    )
    mock_registry.register("unregistered", mock_provider)

    with pytest.raises(Exception, match="Sync upstream failure"):
        await service.sync_account(user_id, account_id)


@pytest.mark.asyncio
async def test_game_service_account_management():
    """Test update_account, set_primary_account, unlink_account, get_account_stats."""
    mock_db = AsyncMock()
    service = GameService(mock_db)

    user_id = uuid.uuid4()
    account_id = uuid.uuid4()
    account = GameAccount(
        id=account_id,
        user_id=user_id,
        platform="steam",
        account_identifier="76561198012345678",
        game_name="Dota 2",
        in_game_name="OldName",
        is_primary=False,
    )

    service.account_repo.get_by_id = AsyncMock(return_value=account)
    service.account_repo.update = AsyncMock(return_value=account)
    service.account_repo.delete = AsyncMock()
    service.account_repo.set_primary_account = AsyncMock(return_value=account)
    service.stat_repo.get_by_account_id = AsyncMock(return_value=[])

    # update_account
    updated = await service.update_account(
        user_id,
        account_id,
        GameAccountUpdateRequest(in_game_name="NewName", tagline="NA1", region="US"),
    )
    assert updated.in_game_name == "NewName"
    assert updated.tagline == "NA1"
    assert updated.region == "US"

    # update_account with is_primary
    updated_primary = await service.update_account(
        user_id,
        account_id,
        GameAccountUpdateRequest(is_primary=True),
    )
    assert updated_primary is not None

    # get_account_stats
    stats = await service.get_account_stats(user_id, account_id)
    assert stats == []

    # unlink_account
    res = await service.unlink_account(user_id, account_id)
    assert res is True
    service.account_repo.delete.assert_called_once_with(account)


# =========================================================================
# Dota2Service Edge Cases
# =========================================================================

@pytest.mark.asyncio
async def test_dota2_service_methods():
    """Test Dota2Service helper methods and edge cases."""
    mock_db = AsyncMock()
    service = Dota2Service(mock_db)

    # 1. get_steam_login_url
    url_resp = service.get_steam_login_url()
    assert "openid.mode=checkid_setup" in url_resp.login_url

    # 2. verify_and_link_steam invalid claimed_id
    with pytest.raises(ValidationException, match="Invalid or missing openid.claimed_id"):
        await service.verify_and_link_steam(uuid.uuid4(), {"openid.claimed_id": "invalid"})

    # 3. get_dota2_profile entity not found
    service.account_repo.get_by_user_and_game = AsyncMock(return_value=[])
    with pytest.raises(EntityNotFoundException, match="No linked Dota 2 account"):
        await service.get_dota2_profile(uuid.uuid4())

    # 4. run_background_dota2_sync executes without crash
    with patch("app.services.dota2_service.async_session_factory") as mock_ctx:
        mock_session = AsyncMock()
        mock_ctx.return_value.__aenter__.return_value = mock_session
        await run_background_dota2_sync(uuid.uuid4(), uuid.uuid4())


# =========================================================================
# RiotService Edge Cases
# =========================================================================

@pytest.mark.asyncio
async def test_riot_service_methods():
    """Test RiotService helper methods and edge cases."""
    mock_db = AsyncMock()
    service = RiotService(mock_db)

    # 1. get_rso_login_url
    url_resp = service.get_rso_login_url(state="test_state")
    assert "test_state" in url_resp.auth_url

    # 2. handle_rso_callback verification failure
    with patch.object(
        service.riot_provider,
        "verify_account",
        new=AsyncMock(
            return_value=AccountVerificationResult(
                is_valid=False,
                account_identifier="",
                in_game_name="",
                error_message="RSO callback verification failed",
            )
        ),
    ):
        with pytest.raises(ValidationException, match="RSO callback verification failed"):
            await service.handle_rso_callback(uuid.uuid4(), "bad_code")

    # 3. get_riot_profile entity not found
    service.account_repo.get_by_user_and_game = AsyncMock(return_value=[])
    with pytest.raises(EntityNotFoundException, match="No linked Riot/Valorant account"):
        await service.get_riot_profile(uuid.uuid4())
