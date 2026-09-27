"""
Unit tests for core services: UserService, AuthService, ProfileService, SurveyService, and DNAService.
"""

from datetime import datetime, timezone
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_refresh_token, get_password_hash, verify_password
from app.models.gamer_dna import GamerDNA
from app.models.gamer_profile import GamerProfile
from app.models.survey_response import SurveyResponse
from app.models.user import User
from app.schemas.auth import (
    TokenRefreshRequest,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.schemas.profile import GamerProfileCreate, GamerProfileUpdate
from app.schemas.survey import SurveyAnswerSubmission, SurveySubmissionRequest
from app.services.auth_service import AuthService
from app.services.dna_service import DNAService
from app.services.profile_service import ProfileService
from app.services.survey_service import SurveyService
from app.services.user_service import UserService


# ==============================================================================
# UserService Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_user_service_create_user():
    """Test UserService.create_user persists user with normalized fields."""
    mock_session = AsyncMock(spec=AsyncSession)
    user_service = UserService(mock_session)

    user = await user_service.create_user(
        username="  AlphaGamer  ",
        email="  ALPHA@SQUADSYNC.GG  ",
        password_hash="hashed_pw_here",
    )

    assert user.username == "AlphaGamer"
    assert user.email == "alpha@squadsync.gg"
    assert user.failed_login_attempts == 0
    assert user.is_locked is False
    assert mock_session.add.called
    assert mock_session.commit.called


@pytest.mark.asyncio
async def test_user_service_failed_attempts_and_lockout():
    """Test UserService increments failed login attempts and locks at threshold."""
    mock_session = AsyncMock(spec=AsyncSession)
    user_service = UserService(mock_session)
    now = datetime.now(timezone.utc)
    user = User(
        id=uuid.uuid4(),
        username="lock_target",
        email="target@squadsync.gg",
        password_hash="fakehash",
        is_active=True,
        is_locked=False,
        failed_login_attempts=4,
        created_at=now,
        updated_at=now,
    )

    attempts = await user_service.record_failed_attempt(user, max_attempts=5)
    assert attempts == 5
    assert user.is_locked is True

    await user_service.reset_failed_attempts(user)
    assert user.failed_login_attempts == 0


# ==============================================================================
# AuthService Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_auth_service_register_duplicate_email():
    """Test AuthService.register raises 409 when email already exists."""
    mock_session = AsyncMock(spec=AsyncSession)
    auth_service = AuthService(mock_session)

    now = datetime.now(timezone.utc)
    existing = User(
        id=uuid.uuid4(),
        username="other_name",
        email="existing@squadsync.gg",
        password_hash="fake",
        is_active=True,
        is_locked=False,
        failed_login_attempts=0,
        created_at=now,
        updated_at=now,
    )
    auth_service.user_service.get_by_email = AsyncMock(return_value=existing)

    reg_dto = UserRegisterRequest(
        username="new_player",
        email="existing@squadsync.gg",
        password="StrongP@ssw0rd123!",
    )
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.register(reg_dto)
    assert exc_info.value.status_code == 409
    assert "email" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_auth_service_register_duplicate_username():
    """Test AuthService.register raises 409 when username already exists."""
    mock_session = AsyncMock(spec=AsyncSession)
    auth_service = AuthService(mock_session)

    now = datetime.now(timezone.utc)
    existing = User(
        id=uuid.uuid4(),
        username="taken_name",
        email="other@squadsync.gg",
        password_hash="fake",
        is_active=True,
        is_locked=False,
        failed_login_attempts=0,
        created_at=now,
        updated_at=now,
    )
    auth_service.user_service.get_by_email = AsyncMock(return_value=None)
    auth_service.user_service.get_by_username = AsyncMock(return_value=existing)

    reg_dto = UserRegisterRequest(
        username="taken_name",
        email="fresh@squadsync.gg",
        password="StrongP@ssw0rd123!",
    )
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.register(reg_dto)
    assert exc_info.value.status_code == 409
    assert "username" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_auth_service_login_success():
    """Test AuthService.login returns JWT access & refresh tokens on valid credentials."""
    mock_session = AsyncMock(spec=AsyncSession)
    auth_service = AuthService(mock_session)

    now = datetime.now(timezone.utc)
    hashed_pw = get_password_hash("ValidPass123!")
    user = User(
        id=uuid.uuid4(),
        username="valid_player",
        email="player@squadsync.gg",
        password_hash=hashed_pw,
        is_active=True,
        is_locked=False,
        failed_login_attempts=0,
        created_at=now,
        updated_at=now,
    )
    auth_service.user_service.get_by_username_or_email = AsyncMock(return_value=user)

    tokens = await auth_service.login(
        UserLoginRequest(username_or_email="valid_player", password="ValidPass123!")
    )
    assert tokens.access_token is not None
    assert tokens.refresh_token is not None
    assert tokens.token_type == "bearer"


@pytest.mark.asyncio
async def test_auth_service_login_bad_password():
    """Test AuthService.login records failed attempt and raises 401 on wrong password."""
    mock_session = AsyncMock(spec=AsyncSession)
    auth_service = AuthService(mock_session)

    now = datetime.now(timezone.utc)
    hashed_pw = get_password_hash("CorrectPass123!")
    user = User(
        id=uuid.uuid4(),
        username="wrong_pw_player",
        email="wrong@squadsync.gg",
        password_hash=hashed_pw,
        is_active=True,
        is_locked=False,
        failed_login_attempts=0,
        created_at=now,
        updated_at=now,
    )
    auth_service.user_service.get_by_username_or_email = AsyncMock(return_value=user)

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.login(
            UserLoginRequest(username_or_email="wrong_pw_player", password="WrongPassword999!")
        )
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_auth_service_forgot_and_reset_password_lifecycle():
    """Test full forgot-password token issuance and password reset sequence."""
    mock_session = AsyncMock(spec=AsyncSession)
    auth_service = AuthService(mock_session)

    now = datetime.now(timezone.utc)
    user = User(
        id=uuid.uuid4(),
        username="reset_user",
        email="reset@squadsync.gg",
        password_hash=get_password_hash("OldPassword123!"),
        is_active=True,
        is_locked=True,
        failed_login_attempts=5,
        created_at=now,
        updated_at=now,
    )
    auth_service.user_service.get_by_email = AsyncMock(return_value=user)
    auth_service.user_service.get_by_id = AsyncMock(return_value=user)

    from app.schemas.auth import ForgotPasswordRequest, ResetPasswordRequest
    forgot_res = await auth_service.forgot_password(
        ForgotPasswordRequest(email="reset@squadsync.gg")
    )
    assert forgot_res.reset_token is not None

    reset_res = await auth_service.reset_password(
        ResetPasswordRequest(
            token=forgot_res.reset_token,
            new_password="NewP@ssword2026!",
        )
    )
    assert "successfully" in reset_res.message.lower()
    assert user.is_locked is False
    assert user.failed_login_attempts == 0
    assert verify_password("NewP@ssword2026!", user.password_hash)


# ==============================================================================
# ProfileService Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_profile_service_crud():
    """Test ProfileService get, create, and update logic."""
    mock_session = AsyncMock(spec=AsyncSession)
    profile_service = ProfileService(mock_session)
    user_id = uuid.uuid4()

    # Get non-existent profile raises 404
    profile_service.get_by_user_id = AsyncMock(return_value=None)
    with pytest.raises(HTTPException) as exc_info:
        await profile_service.get_by_user_id_or_404(user_id)
    assert exc_info.value.status_code == 404

    # Create profile
    create_dto = GamerProfileCreate(
        favorite_game="Valorant",
        rank="Diamond 2",
        preferred_role="Duelist",
        language="English",
        region="NA-East",
        bio="Clutch master",
    )
    profile = await profile_service.create_profile(user_id, create_dto)
    assert profile.favorite_game == "Valorant"
    assert profile.user_id == user_id

    # Update profile
    profile_service.get_by_user_id_or_404 = AsyncMock(return_value=profile)
    update_dto = GamerProfileUpdate(rank="Immortal 1")
    updated = await profile_service.update_profile(user_id, update_dto)
    assert updated.rank == "Immortal 1"


# ==============================================================================
# SurveyService & DNAService Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_survey_service_submit_and_scores():
    """Test SurveyService validates answers and accurately aggregates category points."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    survey_service = SurveyService(mock_session)
    user_id = uuid.uuid4()

    submission = SurveySubmissionRequest(
        answers=[
            SurveyAnswerSubmission(question_id="lead_01", selected_option_id="lead_01_a"),
            SurveyAnswerSubmission(question_id="lead_02", selected_option_id="lead_02_a"),
        ]
    )

    result = await survey_service.submit_survey(user_id, submission)
    assert result.responses_recorded == 2
    assert "Leadership" in result.category_scores


@pytest.mark.asyncio
async def test_dna_service_card_generation():
    """Test DNAService generates full card with strengths and playstyle."""
    mock_session = AsyncMock(spec=AsyncSession)
    dna_service = DNAService(mock_session)
    user_id = uuid.uuid4()

    now = datetime.now(timezone.utc)
    mock_user = User(
        id=user_id,
        username="tactical_ace",
        email="tactical@squadsync.gg",
        password_hash="fake",
        is_active=True,
        is_locked=False,
        failed_login_attempts=0,
        created_at=now,
        updated_at=now,
    )
    mock_profile = GamerProfile(
        id=uuid.uuid4(),
        user_id=user_id,
        favorite_game="CS2",
        rank="Global Elite",
        preferred_role="IGL",
        language="English",
        region="EU-West",
        created_at=now,
        updated_at=now,
    )
    mock_dna = GamerDNA(
        id=uuid.uuid4(),
        user_id=user_id,
        leadership=90,
        communication=85,
        strategy=80,
        teamwork=75,
        aggression=60,
        primary_role="Leader",
        secondary_role="Strategist",
        personality="Commanding In-Game Leader",
        created_at=now,
        updated_at=now,
    )

    dna_service.get_by_user_id_or_404 = AsyncMock(return_value=mock_dna)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_profile
    mock_session.execute.return_value = mock_result

    card = await dna_service.get_gamer_dna_card(mock_user)
    assert card.username == "tactical_ace"
    assert card.primary_role == "Leader"
    assert card.secondary_role == "Strategist"
    assert len(card.strengths) >= 1
    assert len(card.weaknesses) >= 1
    assert card.recommended_playstyle != ""
