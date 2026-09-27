"""
Unit and integration tests for the AI Compatibility Engine.
Validates all 10 comparison dimensions, weighted scoring, risk factor detection,
tactical teaming recommendations, database hydration, and FastAPI endpoints.
"""

from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.compatibility import (
    AICompatibilityConfig,
    AICompatibilityEngine,
    CompetitiveEvaluator,
    LogisticsEvaluator,
    PlayerComparisonInput,
    PsychometricEvaluator,
    default_compatibility_config,
    default_compatibility_engine,
)
from app.main import app
from app.models.gamer_dna import GamerDNA
from app.models.gamer_profile import GamerProfile
from app.models.player_stat import PlayerStat
from app.models.user import User
from app.schemas.compatibility import (
    CompatibilityCompareRequest,
    PlayerProfileComparisonSchema,
)
from app.services.compatibility_service import AICompatibilityService


# ------------------------------------------------------------------------------
# 10 Dimensions Evaluator Unit Tests
# ------------------------------------------------------------------------------

def test_leadership_evaluator_dual_clash_vs_synergy():
    """Test dual high leaders clash, whereas high-low leader pairs produce synergy."""
    evaluator = PsychometricEvaluator()

    # 1. Dual high leaders (both 85+)
    dual_leaders_a = PlayerComparisonInput(leadership=90.0)
    dual_leaders_b = PlayerComparisonInput(leadership=85.0)
    res_dual = evaluator.evaluate(dual_leaders_a, dual_leaders_b, default_compatibility_config)
    l_dim_dual = next(d for d in res_dual if d.dimension == "Leadership")
    assert l_dim_dual.score <= 50.0
    assert "ego clash" in l_dim_dual.assessment.lower() or "dual" in l_dim_dual.assessment.lower()

    # 2. Complementary leader-follower pair (90 and 50)
    comp_a = PlayerComparisonInput(leadership=90.0)
    comp_b = PlayerComparisonInput(leadership=50.0)
    res_comp = evaluator.evaluate(comp_a, comp_b, default_compatibility_config)
    l_dim_comp = next(d for d in res_comp if d.dimension == "Leadership")
    assert l_dim_comp.score >= 90.0
    assert "ideal leader-follower" in l_dim_comp.assessment.lower()


def test_communication_evaluator():
    """Test high communication alignment vs. low communication silence risk."""
    evaluator = PsychometricEvaluator()

    high_comms_a = PlayerComparisonInput(communication=85.0)
    high_comms_b = PlayerComparisonInput(communication=90.0)
    res_high = evaluator.evaluate(high_comms_a, high_comms_b, default_compatibility_config)
    c_dim_high = next(d for d in res_high if d.dimension == "Communication")
    assert c_dim_high.score >= 80.0

    low_comms_a = PlayerComparisonInput(communication=35.0)
    low_comms_b = PlayerComparisonInput(communication=30.0)
    res_low = evaluator.evaluate(low_comms_a, low_comms_b, default_compatibility_config)
    c_dim_low = next(d for d in res_low if d.dimension == "Communication")
    assert c_dim_low.score < 50.0


def test_aggression_and_strategy_evaluator():
    """Test aggression pacing and strategy alignment."""
    evaluator = PsychometricEvaluator()

    p_a = PlayerComparisonInput(aggression=85.0, strategy=80.0)
    p_b = PlayerComparisonInput(aggression=50.0, strategy=85.0)
    res = evaluator.evaluate(p_a, p_b, default_compatibility_config)

    aggr_dim = next(d for d in res if d.dimension == "Aggression")
    strat_dim = next(d for d in res if d.dimension == "Strategy")

    assert aggr_dim.score >= 85.0  # Complementary entry + trade support
    assert strat_dim.score >= 90.0  # Close strategic vision


def test_logistics_region_and_language():
    """Test region matching and language barrier detection."""
    evaluator = LogisticsEvaluator()

    # Same region & language
    p_a = PlayerComparisonInput(region="NA-East", languages=["en", "es"])
    p_b = PlayerComparisonInput(region="NA-East", languages=["en"])
    res_ok = evaluator.evaluate(p_a, p_b, default_compatibility_config)
    reg_ok = next(d for d in res_ok if d.dimension == "Region")
    lang_ok = next(d for d in res_ok if d.dimension == "Language")
    assert reg_ok.score == 100.0
    assert lang_ok.score == 100.0

    # Cross-continental & zero shared languages
    p_x = PlayerComparisonInput(region="NA-East", languages=["en"])
    p_y = PlayerComparisonInput(region="Asia-East", languages=["ko"])
    res_bad = evaluator.evaluate(p_x, p_y, default_compatibility_config)
    reg_bad = next(d for d in res_bad if d.dimension == "Region")
    lang_bad = next(d for d in res_bad if d.dimension == "Language")
    assert reg_bad.score < 30.0
    assert lang_bad.score == 0.0


def test_competitive_rank_win_rate_and_roles():
    """Test rank parity, win rate differential, and role non-clash synergy."""
    evaluator = CompetitiveEvaluator()

    # Complementary roles (Duelist + Controller) and tight rank
    p_a = PlayerComparisonInput(rank_rating=1450, win_rate=56.0, preferred_roles=["Duelist"])
    p_b = PlayerComparisonInput(rank_rating=1420, win_rate=55.0, preferred_roles=["Controller"])
    res_ok = evaluator.evaluate(p_a, p_b, default_compatibility_config)

    rank_ok = next(d for d in res_ok if d.dimension == "Official Rank")
    wr_ok = next(d for d in res_ok if d.dimension == "Win Rate")
    role_ok = next(d for d in res_ok if d.dimension == "Preferred Role")

    assert rank_ok.score >= 95.0
    assert wr_ok.score >= 95.0
    assert role_ok.score == 100.0

    # Direct one-trick clash on Duelist with large rank disparity
    p_clash_a = PlayerComparisonInput(rank_rating=2200, win_rate=65.0, preferred_roles=["Duelist"])
    p_clash_b = PlayerComparisonInput(rank_rating=1000, win_rate=45.0, preferred_roles=["Duelist"])
    res_clash = evaluator.evaluate(p_clash_a, p_clash_b, default_compatibility_config)

    rank_clash = next(d for d in res_clash if d.dimension == "Official Rank")
    role_clash = next(d for d in res_clash if d.dimension == "Preferred Role")

    assert rank_clash.score < 30.0
    assert role_clash.score <= 35.0


# ------------------------------------------------------------------------------
# Engine Synthesis, Strengths, Weaknesses, and Risks Tests
# ------------------------------------------------------------------------------

def test_engine_high_compatibility_duo():
    """Test optimal duo generates high score, strengths, and tactical recommendations."""
    engine = AICompatibilityEngine()

    player_a = PlayerComparisonInput(
        username="VanguardLead",
        leadership=85.0,
        communication=85.0,
        aggression=60.0,
        strategy=85.0,
        region="NA-East",
        languages=["en"],
        schedule_slots=["evening_1", "evening_2"],
        rank_rating=1500,
        win_rate=56.0,
        preferred_roles=["Leader", "Controller"],
    )

    player_b = PlayerComparisonInput(
        username="EntryFragger",
        leadership=50.0,
        communication=80.0,
        aggression=90.0,
        strategy=70.0,
        region="NA-East",
        languages=["en"],
        schedule_slots=["evening_1", "evening_2"],
        rank_rating=1480,
        win_rate=55.5,
        preferred_roles=["Duelist"],
    )

    report = engine.compare(player_a, player_b)

    assert report.compatibility_score >= 80.0
    assert "Optimal" in report.tier or "Strong" in report.tier
    assert len(report.strengths) >= 2
    assert len(report.recommendations) >= 2
    assert len(report.dimension_scores) == 10
    assert not any("CRITICAL LANGUAGE BARRIER" in r for r in report.risk_factors)


def test_engine_detects_all_major_risk_factors():
    """Test engine flags dual leader clash, language barrier, ping, rank disparity, and role clash."""
    engine = AICompatibilityEngine()

    player_a = PlayerComparisonInput(
        username="AlphaLeader",
        leadership=90.0,
        region="NA-East",
        languages=["en"],
        rank_rating=2200,
        win_rate=68.0,
        preferred_roles=["Duelist"],
    )

    player_b = PlayerComparisonInput(
        username="BetaLeader",
        leadership=88.0,
        region="Asia-East",
        languages=["ko"],
        rank_rating=1200,
        win_rate=45.0,
        preferred_roles=["Duelist"],
    )

    report = engine.compare(player_a, player_b)

    assert report.compatibility_score < 50.0
    assert len(report.risk_factors) >= 4
    risk_text = " ".join(report.risk_factors)
    assert "DUAL SHOTCALLER CONFLICT" in risk_text
    assert "CRITICAL LANGUAGE BARRIER" in risk_text
    assert "HIGH LATENCY PENALTY" in risk_text
    assert "ROLE COLLISION" in risk_text


# ------------------------------------------------------------------------------
# Service Layer Tests
# ------------------------------------------------------------------------------

def test_service_compare_payload():
    """Test service handles comparison directly from Pydantic request payload."""
    mock_db = AsyncMock()
    service = AICompatibilityService(db=mock_db)

    req = CompatibilityCompareRequest(
        player_a=PlayerProfileComparisonSchema(
            username="Ace",
            leadership=80.0,
            communication=80.0,
            region="EU-West",
            preferred_roles=["Support"],
        ),
        player_b=PlayerProfileComparisonSchema(
            username="Deuce",
            leadership=50.0,
            communication=75.0,
            region="EU-West",
            preferred_roles=["Duelist"],
        ),
    )

    report = service.compare_payload(req)
    assert report.player_a_name == "Ace"
    assert report.player_b_name == "Deuce"
    assert report.compatibility_score >= 75.0


@pytest.mark.asyncio
async def test_service_compare_users_hydrates_db():
    """Test service fetches both users' DB profiles, DNA, and stats."""
    mock_db = AsyncMock()
    mock_user_repo = AsyncMock()
    mock_profile_repo = AsyncMock()
    mock_dna_repo = AsyncMock()
    mock_stat_repo = AsyncMock()

    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()

    mock_user_repo.get_by_id.side_effect = lambda uid: User(id=uid, username=f"User_{uid}")
    mock_dna_repo.get_by_user_id.return_value = GamerDNA(
        leadership=80, communication=75, aggression=70, strategy=80
    )
    mock_profile_repo.get_by_user_id.return_value = GamerProfile(
        region="NA-East", language="en", preferred_roles=["Controller"]
    )
    mock_stat_repo.get_by_user_id.return_value = [
        PlayerStat(matches_played=50, win_rate=55.0, rank_rating=1400)
    ]

    service = AICompatibilityService(
        db=mock_db,
        user_repo=mock_user_repo,
        profile_repo=mock_profile_repo,
        dna_repo=mock_dna_repo,
        player_stat_repo=mock_stat_repo,
    )

    report = await service.compare_users(user_a_id, user_b_id)
    assert report.compatibility_score > 60.0
    assert len(report.dimension_scores) == 10


@pytest.mark.asyncio
async def test_service_compare_same_user_raises_400():
    """Test comparing a user with themselves raises 400 Bad Request."""
    mock_db = AsyncMock()
    service = AICompatibilityService(db=mock_db)
    same_id = uuid.uuid4()

    with pytest.raises(Exception) as exc_info:
        await service.compare_users(same_id, same_id)
    assert exc_info.value.status_code == 400


# ------------------------------------------------------------------------------
# FastAPI HTTP Endpoint Tests
# ------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_compare_endpoint_http():
    """Test POST /api/v1/compatibility/compare endpoint returns 200 OK."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "player_a": {
                "username": "Player1",
                "leadership": 85.0,
                "communication": 80.0,
                "aggression": 60.0,
                "strategy": 80.0,
                "region": "NA-East",
                "languages": ["en"],
                "rank_rating": 1400,
                "win_rate": 55.0,
                "preferred_roles": ["Leader"],
            },
            "player_b": {
                "username": "Player2",
                "leadership": 50.0,
                "communication": 75.0,
                "aggression": 85.0,
                "strategy": 70.0,
                "region": "NA-East",
                "languages": ["en"],
                "rank_rating": 1420,
                "win_rate": 54.5,
                "preferred_roles": ["Duelist"],
            },
        }

        res = await client.post("/api/v1/compatibility/compare", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert "compatibility_score" in data["data"]
        assert "strengths" in data["data"]
        assert "recommendations" in data["data"]
        assert len(data["data"]["dimension_scores"]) == 10


@pytest.mark.asyncio
async def test_compare_with_user_unauthenticated(client: AsyncClient):
    """Test GET /api/v1/compatibility/compare/{target_user_id} requires auth."""
    random_id = uuid.uuid4()
    res = await client.get(f"/api/v1/compatibility/compare/{random_id}")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_compare_with_user_authenticated_not_found(authenticated_client: AsyncClient):
    """Test GET /api/v1/compatibility/compare/{target_user_id} returns 404 when target user does not exist."""
    random_id = uuid.uuid4()
    res = await authenticated_client.get(f"/api/v1/compatibility/compare/{random_id}")
    assert res.status_code == 404
    data = res.json()
    assert data["success"] is False
    assert "not found" in data["message"].lower()
