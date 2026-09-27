"""
Unit and integration tests for the Squad Recommendation Engine.
Validates Compatibility Score, Role Balance, Skill Balance, Communication,
Leadership Distribution, Top 10 Teammates, Best 5-Player Squad, Missing Roles,
Confidence scoring, CandidateRepository, Service layer, and FastAPI endpoint.
"""

from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.squad_recommendation import (
    LeadershipDistributionEvaluator,
    RoleBalanceEvaluator,
    SkillBalanceEvaluator,
    SquadCommunicationEvaluator,
    SquadRecommendationConfig,
    SquadRecommendationEngine,
    default_squad_config,
)
from app.main import app
from app.models.gamer_dna import GamerDNA
from app.models.gamer_profile import GamerProfile
from app.models.player_stat import PlayerStat
from app.models.user import User
from app.repositories.candidate_repository import CandidateRepository
from app.schemas.matchmaking import MatchmakingCandidate
from app.services.squad_recommendation_service import SquadRecommendationService


# ------------------------------------------------------------------------------
# Evaluator Unit Tests
# ------------------------------------------------------------------------------

def test_role_balance_evaluator():
    """Test Role Balance detects coverage of essential roles and identifies missing ones."""
    evaluator = RoleBalanceEvaluator()

    # Balanced comp with Duelist, Controller, Sentinel, Support, Strategist
    members_full = [
        MatchmakingCandidate(user_id=uuid.uuid4(), username="P1", primary_role="Duelist"),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="P2", primary_role="Controller"),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="P3", primary_role="Sentinel"),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="P4", primary_role="Support"),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="P5", primary_role="Strategist"),
    ]

    score_full, role_dist, missing_full = evaluator.evaluate(members_full, default_squad_config)
    assert score_full == 100.0
    assert len(missing_full) == 0
    assert role_dist["Duelist"] == 1

    # Comp missing Controller and Sentinel (heavy on Duelists)
    members_dupes = [
        MatchmakingCandidate(user_id=uuid.uuid4(), username="P1", primary_role="Duelist"),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="P2", primary_role="Duelist"),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="P3", primary_role="Duelist"),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="P4", primary_role="Support"),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="P5", primary_role="Strategist"),
    ]

    score_dupes, _, missing_dupes = evaluator.evaluate(members_dupes, default_squad_config)
    assert score_dupes < score_full
    assert "Controller" in missing_dupes
    assert "Sentinel" in missing_dupes


def test_skill_balance_evaluator():
    """Test Skill Balance calculates mean MMR, standard deviation, and parity percentage."""
    evaluator = SkillBalanceEvaluator()

    # Tight lobby (all around 1500 MMR)
    tight_members = [
        MatchmakingCandidate(user_id=uuid.uuid4(), username="P1", mmr=1500),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="P2", mmr=1520),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="P3", mmr=1490),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="P4", mmr=1510),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="P5", mmr=1480),
    ]

    score_tight, mean_tight, std_tight = evaluator.evaluate(tight_members)
    assert score_tight >= 90.0
    assert 1490.0 <= mean_tight <= 1510.0
    assert std_tight < 20.0

    # Wide lobby with large MMR disparity
    wide_members = [
        MatchmakingCandidate(user_id=uuid.uuid4(), username="P1", mmr=2200),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="P2", mmr=1000),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="P3", mmr=1500),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="P4", mmr=900),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="P5", mmr=1800),
    ]

    score_wide, _, std_wide = evaluator.evaluate(wide_members)
    assert score_wide < score_tight
    assert std_wide > 400.0


def test_leadership_distribution_evaluator():
    """Test command hierarchy: 1 designated IGL vs. 0 IGLs vs. dual IGL clash."""
    evaluator = LeadershipDistributionEvaluator()

    # 1. Exactly 1 IGL (leadership 88)
    optimal = [
        MatchmakingCandidate(user_id=uuid.uuid4(), username="Captain", leadership=88),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="Follower1", leadership=50),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="Follower2", leadership=60),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="Follower3", leadership=45),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="Follower4", leadership=55),
    ]
    score_opt, igl_opt, assess_opt = evaluator.evaluate(optimal)
    assert score_opt == 100.0
    assert igl_opt == "Captain"
    assert "optimal" in assess_opt.lower()

    # 2. 0 IGLs (all < 75)
    zero_lead = [
        MatchmakingCandidate(user_id=uuid.uuid4(), username=f"P{i}", leadership=50)
        for i in range(5)
    ]
    score_zero, _, assess_zero = evaluator.evaluate(zero_lead)
    assert score_zero == 55.0
    assert "no designated" in assess_zero.lower()

    # 3. Dual clashing IGLs (>=2 players with leadership >= 75)
    clash = [
        MatchmakingCandidate(user_id=uuid.uuid4(), username="Alpha", leadership=85),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="Beta", leadership=82),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="P3", leadership=50),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="P4", leadership=50),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="P5", leadership=50),
    ]
    score_clash, _, assess_clash = evaluator.evaluate(clash)
    assert score_clash == 45.0
    assert "contested" in assess_clash.lower()


# ------------------------------------------------------------------------------
# Engine Synthesis Tests
# ------------------------------------------------------------------------------

def test_engine_top_10_and_best_5_player_squad():
    """Test engine produces Top 10 teammates, best 5-player squad containing Current User, and confidence."""
    engine = SquadRecommendationEngine()

    current_user = MatchmakingCandidate(
        user_id=uuid.uuid4(),
        username="Requester",
        primary_role="Duelist",
        rank="Diamond 1",
        mmr=1500,
        leadership=50,
        communication=80,
        region="NA-East",
        languages=["en"],
    )

    # 15 diverse candidate players
    roles = ["Controller", "Sentinel", "Support", "Strategist", "Leader", "Duelist"]
    candidates = []
    for i in range(15):
        role = roles[i % len(roles)]
        candidates.append(
            MatchmakingCandidate(
                user_id=uuid.uuid4(),
                username=f"Cand_{i}_{role}",
                primary_role=role,
                rank="Diamond 1",
                mmr=1500 + (i * 10),
                leadership=85 if role == "Leader" else 55,
                communication=80,
                region="NA-East",
                languages=["en"],
                preferred_games=["Valorant"],
            )
        )

    result = engine.generate_recommendation(current_user, candidates, game_name="Valorant")

    # 1. Top 10 Teammates
    assert len(result.top_10_teammates) == 10
    # Teammates must be sorted descending by compatibility score
    scores = [t.compatibility_score for t in result.top_10_teammates]
    assert scores == sorted(scores, reverse=True)

    # 2. Best 5-player squad
    assert len(result.best_5_player_squad.members) == 5
    member_ids = [str(m.user_id) for m in result.best_5_player_squad.members]
    assert str(current_user.user_id) in member_ids

    # 3. Calculations
    assert 0.0 <= result.best_5_player_squad.overall_score <= 100.0
    assert 0.0 <= result.best_5_player_squad.role_balance_score <= 100.0
    assert 0.0 <= result.best_5_player_squad.skill_balance_score <= 100.0
    assert 0.0 <= result.best_5_player_squad.communication_score <= 100.0
    assert 0.0 <= result.best_5_player_squad.leadership_score <= 100.0

    # 4. Confidence Score
    assert 0.0 <= result.confidence_score <= 1.0
    assert result.confidence_score >= 0.50

    # 5. Summary narrative
    assert "Requester" in result.summary


# ------------------------------------------------------------------------------
# CandidateRepository Unit Tests
# ------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_candidate_repository_hydration():
    """Test candidate repository correctly builds candidate from user entity."""
    mock_db = AsyncMock()
    repo = CandidateRepository(db=mock_db)

    user = User(
        id=uuid.uuid4(),
        username="db_tester",
        email="test@squadsync.gg",
        password_hash="pw",
    )

    # Mock execute results for profile, dna, stats
    mock_prof = MagicMock()
    mock_prof.scalar_one_or_none.return_value = GamerProfile(
        region="NA-East",
        language="en",
        preferred_games=["Valorant"],
        preferred_roles=["Controller"],
    )
    mock_dna = MagicMock()
    mock_dna.scalar_one_or_none.return_value = GamerDNA(
        leadership=70, communication=80, primary_role="Controller"
    )
    mock_stat = MagicMock()
    mock_stat.scalars.return_value.first.return_value = PlayerStat(
        current_rank="Diamond 2", rank_rating=65, matches_played=80, win_rate=56.0
    )

    mock_db.execute.side_effect = [mock_prof, mock_dna, mock_stat]

    cand = await repo.build_candidate_for_user(user, target_game="Valorant")
    assert cand.username == "db_tester"
    assert cand.region == "NA-East"
    assert cand.primary_role == "Controller"
    assert cand.communication == 80


# ------------------------------------------------------------------------------
# Service Layer Tests
# ------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_squad_recommendation_service_archetype_fallback():
    """Test service falls back to generating tactical archetypes when candidate pool is sparse."""
    mock_db = AsyncMock()
    mock_candidate_repo = AsyncMock()
    mock_user_repo = AsyncMock()

    user_id = uuid.uuid4()
    mock_user_repo.get_by_id.return_value = User(
        id=user_id, username="LoneWolf", email="lone@squadsync.gg", password_hash="hash"
    )
    mock_candidate_repo.build_candidate_for_user.return_value = MatchmakingCandidate(
        user_id=user_id, username="LoneWolf", primary_role="Duelist"
    )
    # Empty DB pool
    mock_candidate_repo.get_candidate_pool.return_value = []

    service = SquadRecommendationService(
        db=mock_db,
        candidate_repo=mock_candidate_repo,
        user_repo=mock_user_repo,
    )

    result = await service.recommend_for_user(user_id=user_id, game_name="Valorant")
    assert len(result.best_5_player_squad.members) == 5
    assert len(result.top_10_teammates) >= 4
    assert result.confidence_score > 0.40


# ------------------------------------------------------------------------------
# FastAPI HTTP Endpoint Tests
# ------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_squad_recommend_endpoint_unauthenticated(client: AsyncClient):
    """Test POST /api/v1/squads/recommend requires authentication."""
    res = await client.post("/api/v1/squads/recommend", json={"game_name": "Valorant"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_squad_recommend_endpoint_authenticated(authenticated_client: AsyncClient):
    """Test POST /api/v1/squads/recommend returns 200 OK and valid response schema."""
    res = await authenticated_client.post(
        "/api/v1/squads/recommend",
        json={"game_name": "Valorant", "candidate_pool_limit": 25},
    )
    if res.status_code != 200:
        print("ACTUAL ERR:", res.json())
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    squad_data = data["data"]
    assert "top_10_teammates" in squad_data
    assert "best_5_player_squad" in squad_data
    assert len(squad_data["best_5_player_squad"]["members"]) == 5
    assert "missing_roles" in squad_data
    assert "confidence_score" in squad_data
    assert "summary" in squad_data
