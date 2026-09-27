"""
Unit tests for Repositories.
Tests BaseRepository, GameAccountRepository, PlayerStatRepository, and ProfileRepository.
"""

from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest

from app.models.game_account import GameAccount
from app.models.gamer_dna import GamerDNA
from app.models.gamer_profile import GamerProfile
from app.models.player_stat import PlayerStat
from app.models.survey_answer import SurveyAnswer
from app.models.user import User
from app.repositories.base import BaseRepository
from app.repositories.dna_repository import DNARepository
from app.repositories.game_account_repository import GameAccountRepository
from app.repositories.player_stat_repository import PlayerStatRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.survey_repository import SurveyRepository
from app.repositories.user_repository import UserRepository


@pytest.mark.asyncio
async def test_base_repository_crud():
    """Test BaseRepository generic CRUD methods."""
    mock_db = AsyncMock()

    test_user = User(
        id=uuid.uuid4(),
        username="repo_user",
        email="repo@squadsync.gg",
        password_hash="hash",
    )
    mock_db.get.return_value = test_user

    repo = BaseRepository(User, mock_db)

    # get_by_id
    res = await repo.get_by_id(test_user.id)
    assert res == test_user
    mock_db.get.assert_called_once_with(User, test_user.id)

    # get_all
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [test_user]
    mock_exec_res = MagicMock()
    mock_exec_res.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_exec_res

    all_users = await repo.get_all(skip=0, limit=10)
    assert len(all_users) == 1
    assert all_users[0] == test_user

    # create
    created = await repo.create(test_user)
    assert created == test_user
    mock_db.add.assert_called_once_with(test_user)
    assert mock_db.commit.call_count >= 1

    # update
    updated = await repo.update(test_user)
    assert updated == test_user

    # delete
    await repo.delete(test_user)
    mock_db.delete.assert_called_once_with(test_user)

    # count
    mock_count_res = MagicMock()
    mock_count_res.scalar_one.return_value = 42
    mock_db.execute.return_value = mock_count_res

    count = await repo.count()
    assert count == 42


@pytest.mark.asyncio
async def test_game_account_repository_queries():
    """Test GameAccountRepository query methods."""
    mock_db = AsyncMock()
    repo = GameAccountRepository(mock_db)

    user_id = uuid.uuid4()
    account_id = uuid.uuid4()
    dummy_acc = GameAccount(
        id=account_id,
        user_id=user_id,
        game_name="Dota 2",
        platform="steam",
        account_identifier="76561198012345678",
        is_primary=True,
    )

    # Mock scalars().all()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [dummy_acc]
    mock_exec_res = MagicMock()
    mock_exec_res.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_exec_res

    # get_by_user_id
    accounts = await repo.get_by_user_id(user_id)
    assert len(accounts) == 1

    # get_by_user_and_game
    game_accounts = await repo.get_by_user_and_game(user_id, "Dota 2")
    assert len(game_accounts) == 1

    # Mock scalar_one_or_none()
    mock_exec_res.scalar_one_or_none.return_value = dummy_acc

    # get_user_account_by_platform
    acc = await repo.get_user_account_by_platform(user_id, "steam", "76561198012345678")
    assert acc == dummy_acc

    # get_by_platform_and_identifier
    acc2 = await repo.get_by_platform_and_identifier("steam", "76561198012345678")
    assert acc2 == dummy_acc

    # get_primary_account
    primary = await repo.get_primary_account(user_id, "Dota 2")
    assert primary == dummy_acc

    # set_primary_account
    mock_db.get.return_value = dummy_acc
    promoted = await repo.set_primary_account(user_id, account_id, "Dota 2")
    assert promoted == dummy_acc
    assert promoted.is_primary is True

    # update_sync_data
    synced = await repo.update_sync_data(
        account_id=account_id,
        raw_data={"test": "data"},
        in_game_name="NewName",
        tagline="NA1",
        region="US",
        is_verified=True,
    )
    assert synced == dummy_acc
    assert synced.in_game_name == "NewName"
    assert synced.tagline == "NA1"
    assert synced.region == "US"


@pytest.mark.asyncio
async def test_player_stat_repository_queries():
    """Test PlayerStatRepository persistence and querying."""
    mock_db = AsyncMock()
    repo = PlayerStatRepository(mock_db)

    acc_id = uuid.uuid4()
    user_id = uuid.uuid4()
    stat = PlayerStat(
        game_account_id=acc_id,
        user_id=user_id,
        season="Season 1",
        game_mode="ranked",
        rank="Immortal",
    )

    # get_by_account_id
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [stat]
    mock_exec_res = MagicMock()
    mock_exec_res.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_exec_res

    stats = await repo.get_by_account_id(acc_id)
    assert len(stats) == 1

    # get_by_user_id
    user_stats = await repo.get_by_user_id(user_id)
    assert len(user_stats) == 1

    # get_by_account_season_mode
    mock_exec_res.scalar_one_or_none.return_value = stat
    mode_stat = await repo.get_by_account_season_mode(acc_id, "Season 1", "ranked")
    assert mode_stat == stat

    # upsert_stat - existing
    updated_stat = await repo.upsert_stat(
        game_account_id=acc_id,
        user_id=user_id,
        season="Season 1",
        game_mode="ranked",
        stat_attributes={"rank": "Immortal #1", "wins": 100},
    )
    assert updated_stat.rank == "Immortal #1"
    assert updated_stat.wins == 100

    # upsert_stat - new
    mock_exec_res.scalar_one_or_none.return_value = None
    new_stat = await repo.upsert_stat(
        game_account_id=acc_id,
        user_id=user_id,
        season="Season 2",
        game_mode="unranked",
        stat_attributes={"rank": "Unranked"},
    )
    assert new_stat.season == "Season 2"
    mock_db.add.assert_called()


@pytest.mark.asyncio
async def test_profile_repository_queries():
    """Test ProfileRepository queries."""
    mock_db = AsyncMock()
    repo = ProfileRepository(mock_db)

    user_id = uuid.uuid4()
    profile = GamerProfile(
        id=uuid.uuid4(),
        user_id=user_id,
        display_name="ProfileMaster",
        region="NA",
        bio="Hello world",
    )

    mock_exec_res = MagicMock()
    mock_exec_res.scalar_one_or_none.return_value = profile
    mock_db.execute.return_value = mock_exec_res

    # get_by_user_id
    p1 = await repo.get_by_user_id(user_id)
    assert p1 == profile

    # save_profile
    saved = await repo.save_profile(profile)
    assert saved == profile
    mock_db.add.assert_called_with(profile)

    # update_profile
    updated = await repo.update_profile(profile, {"bio": "Updated bio"})
    assert updated == profile
    assert profile.bio == "Updated bio"

    # delete_profile
    await repo.delete_profile(profile)
    mock_db.delete.assert_called_with(profile)


@pytest.mark.asyncio
async def test_user_repository_queries():
    """Test UserRepository query and state management methods."""
    mock_db = AsyncMock()
    repo = UserRepository(mock_db)

    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        username="TestUser",
        email="test@squadsync.gg",
        password_hash="hash",
        failed_login_attempts=0,
        is_locked=False,
    )

    mock_exec_res = MagicMock()
    mock_exec_res.scalar_one_or_none.return_value = user
    mock_db.execute.return_value = mock_exec_res

    # get_by_email
    u1 = await repo.get_by_email("test@squadsync.gg")
    assert u1 == user

    # get_by_username
    u2 = await repo.get_by_username("TestUser")
    assert u2 == user

    # get_by_username_or_email
    u3 = await repo.get_by_username_or_email("TestUser")
    assert u3 == user

    # record_failed_attempt
    attempts = await repo.record_failed_attempt(user, max_attempts=5)
    assert attempts == 1
    assert user.is_locked is False

    # lock user after 5
    user.failed_login_attempts = 4
    attempts_locked = await repo.record_failed_attempt(user, max_attempts=5)
    assert attempts_locked == 5
    assert user.is_locked is True

    # reset_failed_attempts
    await repo.reset_failed_attempts(user)
    assert user.failed_login_attempts == 0


@pytest.mark.asyncio
async def test_survey_repository_queries():
    """Test SurveyRepository query and bulk persistence methods."""
    mock_db = AsyncMock()
    repo = SurveyRepository(mock_db)

    user_id = uuid.uuid4()
    ans1 = SurveyAnswer(
        id=uuid.uuid4(),
        user_id=user_id,
        question_id="lead_01",
        category="Leadership",
        answer="I take charge",
        score=5,
    )

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [ans1]
    mock_exec_res = MagicMock()
    mock_exec_res.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_exec_res

    answers = await repo.get_answers_by_user_id(user_id)
    assert len(answers) == 1
    assert answers[0] == ans1

    saved = await repo.save_answers([ans1])
    assert len(saved) == 1
    mock_db.add.assert_called_with(ans1)


@pytest.mark.asyncio
async def test_dna_repository_queries():
    """Test DNARepository query and upsert methods."""
    mock_db = AsyncMock()
    repo = DNARepository(mock_db)

    user_id = uuid.uuid4()
    dna = GamerDNA(
        id=uuid.uuid4(),
        user_id=user_id,
        primary_role="Leader",
        personality="Tactical Shotcaller",
        confidence=80,
    )

    mock_exec_res = MagicMock()
    mock_exec_res.scalar_one_or_none.return_value = dna
    mock_db.execute.return_value = mock_exec_res

    res = await repo.get_by_user_id(user_id)
    assert res == dna

    # Upsert existing
    upserted = await repo.upsert_dna(dna)
    assert upserted == dna
    assert upserted.primary_role == "Leader"

    # Upsert new
    mock_exec_res.scalar_one_or_none.return_value = None
    new_dna = GamerDNA(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        primary_role="Support",
        personality="Anchor",
        confidence=60,
    )
    res_new = await repo.upsert_dna(new_dna)
    assert res_new == new_dna
    mock_db.add.assert_called()

