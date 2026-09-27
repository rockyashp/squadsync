"""
Pytest test suite for AI Explanation Engine.
Tests template-based generation, engine logic, service layer, and FastAPI endpoints.
"""

from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest
from httpx import AsyncClient

from app.core.compatibility.models import CompatibilityReport
from app.core.explanation.config import ExplanationConfig
from app.core.explanation.engine import (
    AIExplanationEngine,
    ExplanationResult,
    PlayerExplanationContext,
)
from app.models.gamer_dna import GamerDNA
from app.models.gamer_profile import GamerProfile
from app.models.player_stat import PlayerStat
from app.models.user import User
from app.repositories.dna_repository import DNARepository
from app.repositories.player_stat_repository import PlayerStatRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.explanation import (
    ExplanationCompareRequest,
    ExplanationResponse,
    PlayerExplanationInputSchema,
)
from app.services.explanation_service import AIExplanationService


# ==============================================================================
# 1. AIExplanationEngine Unit Tests
# ==============================================================================

def test_explanation_engine_high_compatibility_match():
    """Test engine generates rich positive match reasons, strengths, and coaching tips for complementary duo."""
    engine = AIExplanationEngine()

    p_a = PlayerExplanationContext(
        username="ViperIGL",
        leadership=85.0,
        communication=85.0,
        aggression=55.0,
        strategy=90.0,
        teamwork=80.0,
        primary_role="Controller",
        secondary_role="Leader",
        preferred_roles=["Controller", "Leader"],
        rank="Diamond 3",
        rank_rating=1450,
        win_rate=56.5,
        matches_played=70,
        region="NA-East",
        languages=["en"],
        schedule_slots=["weekday_evening"],
    )

    p_b = PlayerExplanationContext(
        username="JettEntry",
        leadership=40.0,
        communication=75.0,
        aggression=92.0,
        strategy=65.0,
        teamwork=70.0,
        primary_role="Duelist",
        secondary_role="Initiator",
        preferred_roles=["Duelist"],
        rank="Diamond 2",
        rank_rating=1400,
        win_rate=57.0,
        matches_played=80,
        region="NA-East",
        languages=["en"],
        schedule_slots=["weekday_evening"],
    )

    report = CompatibilityReport(
        player_a_name="ViperIGL",
        player_b_name="JettEntry",
        compatibility_score=91.5,
        tier="Optimal Duo Synergy",
        dimension_scores={
            "leadership": 95.0,
            "communication": 85.0,
            "aggression": 88.0,
            "strategy": 82.0,
            "preferred_role": 100.0,
            "official_rank": 95.0,
            "region": 100.0,
            "language": 100.0,
            "schedule": 90.0,
            "win_rate": 92.0,
        },
        strengths=["Clear command hierarchy", "Complementary agent pool"],
        weaknesses=[],
        recommendations=["Designate ViperIGL as default caller"],
        risk_factors=[],
    )

    result = engine.generate_explanation(p_a, p_b, report)

    assert isinstance(result, ExplanationResult)
    assert "Optimal" in result.headline or "Synergy" in result.headline
    assert result.compatibility_score == 91.5
    assert result.tier == "Optimal Duo Synergy"

    # Why they match assertions
    match_text = " ".join(result.match_reasons)
    assert "ViperIGL" in match_text
    assert "command hierarchy" in match_text or "shotcalling" in match_text
    assert "communication" in match_text.lower() or "situational awareness" in match_text.lower()
    assert "tactical role synergy" in match_text.lower() or "controller" in match_text.lower()

    # Strengths assertions
    strengths_text = " ".join(result.strengths_narrative)
    assert "Controller" in strengths_text or "Duelist" in strengths_text
    assert "command dynamic" in strengths_text.lower() or "shotcaller" in strengths_text.lower()

    # Improvement advice assertions
    assert len(result.improvement_suggestions) > 0
    assert result.confidence_score >= 0.85


def test_explanation_engine_dual_leadership_ego_clash():
    """Test engine detects dual-shotcaller ego friction and recommends clear IGL protocol."""
    engine = AIExplanationEngine()

    p_a = PlayerExplanationContext(
        username="AlphaLeader",
        leadership=90.0,
        communication=75.0,
        aggression=70.0,
        primary_role="Leader",
        rank_rating=1200,
    )
    p_b = PlayerExplanationContext(
        username="BravoLeader",
        leadership=88.0,
        communication=72.0,
        aggression=68.0,
        primary_role="Strategist",
        rank_rating=1250,
    )

    result = engine.generate_explanation(p_a, p_b)

    mismatch_text = " ".join(result.mismatch_reasons)
    assert "Dual-shotcaller" in mismatch_text or "friction" in mismatch_text.lower()
    assert "AlphaLeader" in mismatch_text
    assert "BravoLeader" in mismatch_text

    weakness_text = " ".join(result.weaknesses_narrative)
    assert "shotcall disputes" in weakness_text.lower() or "ego" in weakness_text.lower()

    suggestions_text = " ".join(result.improvement_suggestions)
    assert "In-Game Leader" in suggestions_text or "IGL" in suggestions_text


def test_explanation_engine_role_collision():
    """Test engine flags identical primary roles and suggests role flexing."""
    engine = AIExplanationEngine()

    p_a = PlayerExplanationContext(
        username="ReynaOneTrick",
        leadership=50.0,
        communication=60.0,
        primary_role="Duelist",
        preferred_roles=["Duelist"],
    )
    p_b = PlayerExplanationContext(
        username="JettOneTrick",
        leadership=55.0,
        communication=65.0,
        primary_role="Duelist",
        preferred_roles=["Duelist", "Initiator"],
    )

    result = engine.generate_explanation(p_a, p_b)

    mismatch_text = " ".join(result.mismatch_reasons)
    assert "role collision" in mismatch_text.lower() or "Duelist" in mismatch_text

    weakness_text = " ".join(result.weaknesses_narrative)
    assert "flexibility" in weakness_text.lower() or "Duelist" in weakness_text

    suggestions_text = " ".join(result.improvement_suggestions)
    assert "Cross-train secondary roles" in suggestions_text or "flex" in suggestions_text.lower()


def test_explanation_engine_skill_disparity_and_silent_comms():
    """Test engine flags severe rank gap, non-vocal communication, and regional disconnect."""
    engine = AIExplanationEngine()

    p_a = PlayerExplanationContext(
        username="RadiantPro",
        leadership=40.0,
        communication=35.0,
        primary_role="Duelist",
        rank="Radiant",
        rank_rating=2200,
        win_rate=68.0,
        region="NA-East",
        languages=["en"],
    )
    p_b = PlayerExplanationContext(
        username="SilverCasual",
        leadership=38.0,
        communication=30.0,
        primary_role="Initiator",
        rank="Silver 2",
        rank_rating=950,
        win_rate=48.0,
        region="EU-West",
        languages=["de"],
    )

    result = engine.generate_explanation(p_a, p_b)

    mismatch_text = " ".join(result.mismatch_reasons)
    # Checks for skill gap, comms deficit, region mismatch, or language disconnect
    assert "skill disparity" in mismatch_text.lower() or "MMR gap" in mismatch_text
    assert "communication" in mismatch_text.lower() or "silent" in mismatch_text.lower()
    assert "logistical barrier" in mismatch_text.lower() or "language" in mismatch_text.lower()

    weakness_text = " ".join(result.weaknesses_narrative)
    assert "information bottlenecks" in weakness_text.lower() or "skill expectation" in weakness_text.lower()


# ==============================================================================
# 2. AIExplanationService Unit Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_explanation_service_payload():
    """Test service processes explicit request payload without database calls."""
    mock_db = AsyncMock()
    service = AIExplanationService(db=mock_db)

    req = ExplanationCompareRequest(
        player_a=PlayerExplanationInputSchema(
            username="AstraMain",
            leadership=75.0,
            communication=80.0,
            aggression=50.0,
            strategy=85.0,
            primary_role="Controller",
            rank="Ascendant 1",
            rank_rating=1650,
            region="NA-East",
            languages=["en"],
        ),
        player_b=PlayerExplanationInputSchema(
            username="SovaDart",
            leadership=60.0,
            communication=82.0,
            aggression=60.0,
            strategy=80.0,
            primary_role="Initiator",
            rank="Ascendant 2",
            rank_rating=1680,
            region="NA-East",
            languages=["en"],
        ),
    )

    res = service.explain_payload(req)

    assert isinstance(res, ExplanationResponse)
    assert res.player_a_name == "AstraMain"
    assert res.player_b_name == "SovaDart"
    assert len(res.why_they_match) > 0
    assert len(res.strengths) > 0
    assert len(res.improvement_suggestions) > 0
    assert 0.0 <= res.compatibility_score <= 100.0


@pytest.mark.asyncio
async def test_explanation_service_same_user_forbidden():
    """Test service rejects comparing a user with themselves with 400 Bad Request."""
    mock_db = AsyncMock()
    service = AIExplanationService(db=mock_db)

    uid = uuid.uuid4()
    with pytest.raises(Exception) as exc_info:
        await service.explain_between_users(user_a_id=uid, user_b_id=uid)
    assert "Cannot generate compatibility explanation for a user with themselves" in str(exc_info.value)


@pytest.mark.asyncio
async def test_explanation_service_hydration_from_database():
    """Test service successfully hydrates User, GamerProfile, GamerDNA, and Stats from DB."""
    mock_db = AsyncMock()
    user_repo = AsyncMock(spec=UserRepository)
    profile_repo = AsyncMock(spec=ProfileRepository)
    dna_repo = AsyncMock(spec=DNARepository)
    stat_repo = AsyncMock(spec=PlayerStatRepository)

    uid_a = uuid.uuid4()
    uid_b = uuid.uuid4()

    user_a = User(id=uid_a, username="db_phoenix", email="a@gg.com", password_hash="pw")
    user_b = User(id=uid_b, username="db_brimstone", email="b@gg.com", password_hash="pw")

    user_repo.get_by_id.side_effect = lambda u_id: user_a if u_id == uid_a else user_b

    profile_repo.get_by_user_id.side_effect = lambda u_id: (
        GamerProfile(user_id=u_id, region="NA-East", language="en", preferred_roles=["Duelist"])
        if u_id == uid_a
        else GamerProfile(user_id=u_id, region="NA-East", language="en", preferred_roles=["Controller"])
    )

    dna_repo.get_by_user_id.side_effect = lambda u_id: (
        GamerDNA(user_id=u_id, leadership=45, communication=75, aggression=85, primary_role="Duelist")
        if u_id == uid_a
        else GamerDNA(user_id=u_id, leadership=85, communication=80, aggression=55, primary_role="Controller")
    )

    stat_repo.get_by_user_id.side_effect = lambda u_id: [
        PlayerStat(user_id=u_id, current_rank="Diamond 1", rank_rating=60, matches_played=50, win_rate=54.0)
    ]

    service = AIExplanationService(
        db=mock_db,
        user_repo=user_repo,
        profile_repo=profile_repo,
        dna_repo=dna_repo,
        player_stat_repo=stat_repo,
    )

    res = await service.explain_between_users(uid_a, uid_b)

    assert isinstance(res, ExplanationResponse)
    assert res.player_a_name == "db_phoenix"
    assert res.player_b_name == "db_brimstone"
    assert len(res.why_they_match) > 0
    assert len(res.strengths) > 0


# ==============================================================================
# 3. FastAPI HTTP Endpoint Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_explain_payload_endpoint(client: AsyncClient):
    """Test POST /api/v1/explanation/compare generates 200 OK without requiring authentication."""
    body = {
        "player_a": {
            "username": "BreachMain",
            "leadership": 65.0,
            "communication": 75.0,
            "aggression": 80.0,
            "strategy": 70.0,
            "primary_role": "Initiator",
            "rank": "Platinum 3",
            "rank_rating": 1250,
        },
        "player_b": {
            "username": "CypherMain",
            "leadership": 70.0,
            "communication": 78.0,
            "aggression": 45.0,
            "strategy": 88.0,
            "primary_role": "Sentinel",
            "rank": "Platinum 2",
            "rank_rating": 1200,
        },
    }

    res = await client.post("/api/v1/explanation/compare", json=body)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    explanation = data["data"]
    assert "headline" in explanation
    assert "why_they_match" in explanation
    assert "why_they_dont_match" in explanation
    assert "strengths" in explanation
    assert "weaknesses" in explanation
    assert "improvement_suggestions" in explanation
    assert "confidence_score" in explanation


@pytest.mark.asyncio
async def test_explain_users_endpoint_unauthenticated(client: AsyncClient):
    """Test GET /api/v1/explanation/users/{id} requires authentication (401)."""
    random_id = uuid.uuid4()
    res = await client.get(f"/api/v1/explanation/users/{random_id}")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_explain_users_endpoint_authenticated(authenticated_client: AsyncClient):
    """Test GET /api/v1/explanation/users/{id} with authenticated user returns 404 for unknown user or 200."""
    random_id = uuid.uuid4()
    res = await authenticated_client.get(f"/api/v1/explanation/users/{random_id}")
    # Unknown target user triggers 404
    assert res.status_code == 404
