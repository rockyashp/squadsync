"""
Unit and integration tests for the Skill Profile Generator.
Validates all 6 competitive skill dimensions, explainable score rationales,
tier classification, radar chart geometry, service database hydration, and FastAPI endpoints.
"""

from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.role_classifier.features import GamerDNAVector, OfficialGameStats
from app.core.skill_profile import (
    CommunicationEvaluator,
    ConsistencyEvaluator,
    DecisionMakingEvaluator,
    GameSenseEvaluator,
    LeadershipEvaluator,
    MechanicalSkillEvaluator,
    SkillProfileConfig,
    SkillProfileEngine,
    SkillTier,
    default_skill_config,
    default_skill_engine,
)
from app.main import app
from app.models.gamer_dna import GamerDNA
from app.models.player_stat import PlayerStat
from app.models.survey_answer import SurveyAnswer
from app.schemas.role_classifier import GamerDNAInput, OfficialGameStatsInput
from app.schemas.skill_profile import SkillProfileEvaluateRequest
from app.services.skill_profile_service import SkillProfileService


# ------------------------------------------------------------------------------
# Configuration & Tier Mapping Tests
# ------------------------------------------------------------------------------

def test_skill_tier_thresholds():
    """Verify tier assignment across score spectrum."""
    cfg = default_skill_config
    assert cfg.get_tier(92.0) == SkillTier.S_TIER
    assert cfg.get_tier(78.5) == SkillTier.A_TIER
    assert cfg.get_tier(62.0) == SkillTier.B_TIER
    assert cfg.get_tier(45.0) == SkillTier.C_TIER
    assert cfg.get_tier(30.0) == SkillTier.D_TIER


# ------------------------------------------------------------------------------
# Evaluator Unit Tests for all 6 Dimensions
# ------------------------------------------------------------------------------

def test_mechanical_skill_evaluator():
    """Test Mechanical Skill reflects aim accuracy, lethal conversion, and aggression."""
    evaluator = MechanicalSkillEvaluator()
    dna = GamerDNAVector(aggression=90.0, confidence=85.0)
    stats = OfficialGameStats(kd_ratio=1.65, headshot_pct=34.0, win_rate=58.0)

    result = evaluator.evaluate(dna, stats, default_skill_config)
    assert result.name == "Mechanical Skill"
    assert result.score >= 70.0
    assert "34.0% headshot accuracy" in result.explanation
    assert "1.65 K/D" in result.explanation
    assert "dna_contribution" in result.signal_breakdown
    assert "telemetry_contribution" in result.signal_breakdown


def test_communication_evaluator():
    """Test Communication reflects survey comms, teamwork, and assist conversion."""
    evaluator = CommunicationEvaluator()
    dna = GamerDNAVector(communication=92.0, teamwork=88.0)
    stats = OfficialGameStats(kda=3.4, win_rate=56.0)

    result = evaluator.evaluate(dna, stats, default_skill_config)
    assert result.name == "Communication"
    assert result.score >= 70.0
    assert "92/100" in result.explanation
    assert "KDA 3.40" in result.explanation


def test_leadership_evaluator():
    """Test Leadership reflects shotcalling, win rate leverage, and composure."""
    evaluator = LeadershipEvaluator()
    dna = GamerDNAVector(leadership=95.0, confidence=90.0)
    stats = OfficialGameStats(win_rate=62.0, matches_played=85)

    result = evaluator.evaluate(dna, stats, default_skill_config)
    assert result.name == "Leadership"
    assert result.score >= 75.0
    assert "62.0%" in result.explanation
    assert "95/100" in result.explanation


def test_consistency_evaluator():
    """Test Consistency evaluates low performance volatility and match experience."""
    evaluator = ConsistencyEvaluator()
    dna = GamerDNAVector(teamwork=85.0, strategy=80.0, aggression=50.0)
    stats = OfficialGameStats(matches_played=120, kd_ratio=1.15, win_rate=54.0)

    result = evaluator.evaluate(dna, stats, default_skill_config)
    assert result.name == "Consistency"
    assert result.score >= 60.0
    assert "120 games" in result.explanation


def test_decision_making_evaluator():
    """Test Decision Making evaluates risk-reward assessment and survivability."""
    evaluator = DecisionMakingEvaluator()
    dna = GamerDNAVector(strategy=90.0, teamwork=82.0)
    stats = OfficialGameStats(kda=2.8, win_rate=57.0, kd_ratio=1.2)

    result = evaluator.evaluate(dna, stats, default_skill_config)
    assert result.name == "Decision Making"
    assert result.score >= 65.0
    assert "strategic psychometrics" in result.explanation.lower()


def test_game_sense_evaluator():
    """Test Game Sense evaluates macro map reading, anticipation, and rotation timing."""
    evaluator = GameSenseEvaluator()
    dna = GamerDNAVector(strategy=92.0, communication=80.0, leadership=75.0)
    stats = OfficialGameStats(win_rate=59.0, kd_ratio=1.25, kda=2.6)

    result = evaluator.evaluate(dna, stats, default_skill_config)
    assert result.name == "Game Sense"
    assert result.score >= 68.0
    assert "macro strategy" in result.explanation.lower()


# ------------------------------------------------------------------------------
# Engine Synthesis Tests
# ------------------------------------------------------------------------------

def test_skill_profile_engine_synthesis():
    """Test full engine generates radar chart, overall score, strengths, and growth areas."""
    engine = SkillProfileEngine()
    dna = GamerDNAVector(
        leadership=88.0,
        communication=82.0,
        strategy=90.0,
        teamwork=75.0,
        aggression=65.0,
        confidence=80.0,
    )
    stats = OfficialGameStats(
        win_rate=58.0,
        kd_ratio=1.35,
        kda=2.5,
        matches_played=95,
        headshot_pct=26.0,
    )

    profile = engine.generate(dna, stats)

    assert 0.0 <= profile.overall_score <= 100.0
    assert profile.overall_tier is not None
    assert len(profile.radar_chart) == 6
    assert "Mechanical Skill" in profile.radar_chart
    assert "Game Sense" in profile.radar_chart
    assert len(profile.top_strengths) == 2
    assert len(profile.growth_areas) == 2

    # Verify each dimension has an explanation
    for dim in [
        profile.mechanical_skill,
        profile.communication,
        profile.leadership,
        profile.consistency,
        profile.decision_making,
        profile.game_sense,
    ]:
        assert len(dim.explanation) > 20
        assert dim.tier is not None


# ------------------------------------------------------------------------------
# Service Layer Tests
# ------------------------------------------------------------------------------

def test_service_evaluate_payload():
    """Test service evaluation directly from Pydantic request payload."""
    mock_db = AsyncMock()
    service = SkillProfileService(db=mock_db)

    req = SkillProfileEvaluateRequest(
        gamer_dna=GamerDNAInput(
            leadership=85.0,
            communication=80.0,
            strategy=75.0,
            aggression=90.0,
            confidence=85.0,
        ),
        official_stats=OfficialGameStatsInput(
            win_rate=57.0,
            kd_ratio=1.4,
            kda=2.2,
            matches_played=60,
            headshot_pct=28.0,
        ),
    )

    result = service.evaluate_payload(req)
    assert result.overall_score > 60.0
    assert result.mechanical_skill.score > 65.0


@pytest.mark.asyncio
async def test_service_generate_for_user_persists_to_db():
    """Test service hydrates stored user DNA and player stats and updates GamerDNA."""
    user_id = uuid.uuid4()
    mock_db = AsyncMock()
    mock_dna_repo = AsyncMock()
    mock_stat_repo = AsyncMock()
    mock_survey_repo = AsyncMock()

    mock_dna_repo.get_by_user_id.return_value = GamerDNA(
        id=uuid.uuid4(),
        user_id=user_id,
        leadership=80,
        communication=75,
        strategy=85,
        teamwork=70,
        aggression=80,
        confidence=80,
        primary_role="Strategist",
        personality="The Mastermind Tactician",
    )
    mock_stat_repo.get_by_user_id.return_value = [
        PlayerStat(
            id=uuid.uuid4(),
            user_id=user_id,
            game_account_id=uuid.uuid4(),
            season="S2",
            game_mode="competitive",
            matches_played=40,
            win_rate=55.0,
            kd_ratio=1.2,
            kda=2.0,
            headshot_pct=22.0,
        )
    ]

    service = SkillProfileService(
        db=mock_db,
        dna_repo=mock_dna_repo,
        player_stat_repo=mock_stat_repo,
        survey_repo=mock_survey_repo,
    )

    result = await service.generate_for_user(user_id=user_id, persist=True)
    assert result.overall_score > 50.0
    assert mock_dna_repo.update.called


@pytest.mark.asyncio
async def test_service_generate_for_user_survey_fallback():
    """Test service falls back to survey responses when GamerDNA entity is missing."""
    user_id = uuid.uuid4()
    mock_db = AsyncMock()
    mock_dna_repo = AsyncMock()
    mock_stat_repo = AsyncMock()
    mock_survey_repo = AsyncMock()

    # DNA is None
    mock_dna_repo.get_by_user_id.return_value = None

    # Survey answers present
    ans1 = MagicMock()
    ans1.category = "Leadership"
    ans1.score = 80
    ans2 = MagicMock()
    ans2.category = "Strategy"
    ans2.score = 90
    mock_survey_repo.get_answers_by_user_id.return_value = [ans1, ans2]
    mock_stat_repo.get_by_user_id.return_value = []

    service = SkillProfileService(
        db=mock_db,
        dna_repo=mock_dna_repo,
        player_stat_repo=mock_stat_repo,
        survey_repo=mock_survey_repo,
    )

    result = await service.generate_for_user(user_id=user_id, persist=True)
    assert result.leadership.score > 50.0
    assert mock_dna_repo.create.called


# ------------------------------------------------------------------------------
# FastAPI HTTP Endpoint Tests
# ------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_evaluate_skills_endpoint_http():
    """Test POST /api/v1/skills/evaluate endpoint returns 200 OK and valid schema."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "gamer_dna": {
                "leadership": 82.0,
                "communication": 78.0,
                "strategy": 85.0,
                "aggression": 70.0,
                "teamwork": 75.0,
                "confidence": 80.0,
            },
            "official_stats": {
                "win_rate": 57.5,
                "kd_ratio": 1.25,
                "kda": 2.3,
                "matches_played": 80,
                "headshot_pct": 25.0,
            },
        }
        res = await client.post("/api/v1/skills/evaluate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert "overall_score" in data["data"]
        assert "mechanical_skill" in data["data"]
        assert "communication" in data["data"]
        assert "leadership" in data["data"]
        assert "consistency" in data["data"]
        assert "decision_making" in data["data"]
        assert "game_sense" in data["data"]
        assert "radar_chart" in data["data"]
        assert len(data["data"]["top_strengths"]) == 2


@pytest.mark.asyncio
async def test_get_my_skills_unauthenticated(client: AsyncClient):
    """Test GET /api/v1/skills/me requires authentication (401 Unauthorized)."""
    response = await client.get("/api/v1/skills/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_my_skills_authenticated(authenticated_client: AsyncClient):
    """Test GET /api/v1/skills/me succeeds for authenticated user."""
    response = await authenticated_client.get("/api/v1/skills/me")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "overall_score" in data["data"]
    assert "radar_chart" in data["data"]


@pytest.mark.asyncio
async def test_generate_my_skills_authenticated(authenticated_client: AsyncClient):
    """Test POST /api/v1/skills/generate generates and persists skill profile."""
    response = await authenticated_client.post("/api/v1/skills/generate")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "overall_score" in data["data"]
    assert len(data["data"]["top_strengths"]) == 2
