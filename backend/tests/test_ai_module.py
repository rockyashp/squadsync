"""
Pytest test suite for the unified FastAPI AI Module.
Tests the 7 consolidated AI endpoints:
- GET /dna/me
- GET /role/me
- GET /skill-profile
- GET /compatibility/{user_id}
- GET /recommendations
- GET /squad
- GET /explanation/{user_id}
"""

from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest
from httpx import AsyncClient

from app.models.gamer_dna import GamerDNA
from app.models.user import User
from app.schemas.ai import (
    CompatibilityMeResponse,
    ExplanationMeResponse,
    GamerDNAMeResponse,
    RecommendationsMeResponse,
    RoleClassificationMeResponse,
    SkillProfileMeResponse,
    SquadMeResponse,
)
from app.schemas.dna import GamerDNACardResponse
from app.services.ai_service import AIService


# ==============================================================================
# 1. Unauthenticated Security Checks (401 Unauthorized)
# ==============================================================================

@pytest.mark.asyncio
async def test_ai_endpoints_unauthenticated(client: AsyncClient):
    """Verifies that all 7 AI endpoints require authentication and reject unauthenticated requests."""
    random_id = uuid.uuid4()
    endpoints = [
        "/dna/me",
        "/role/me",
        "/skill-profile",
        f"/compatibility/{random_id}",
        "/recommendations",
        "/squad",
        f"/explanation/{random_id}",
        # Also test versioned /api/v1/ai/... paths
        "/api/v1/ai/dna/me",
        "/api/v1/ai/role/me",
        "/api/v1/ai/skill-profile",
        f"/api/v1/ai/compatibility/{random_id}",
        "/api/v1/ai/recommendations",
        "/api/v1/ai/squad",
        f"/api/v1/ai/explanation/{random_id}",
    ]

    for ep in endpoints:
        res = await client.get(ep)
        assert res.status_code == 401, f"Expected 401 for unauthenticated {ep}, got {res.status_code}"


# ==============================================================================
# 2. Authenticated Endpoint Execution Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_ai_dna_me_authenticated(authenticated_client: AsyncClient):
    """Test GET /dna/me returns 404 (if not completed) or 200 with valid schema."""
    res = await authenticated_client.get("/dna/me")
    # For default mock_user without survey, returns 404
    assert res.status_code in (200, 404)
    if res.status_code == 200:
        data = res.json()
        assert data["success"] is True
        assert "dna" in data["data"]


@pytest.mark.asyncio
async def test_ai_role_me_authenticated(authenticated_client: AsyncClient):
    """Test GET /role/me generates AI Role Classification with 200 OK."""
    res = await authenticated_client.get("/role/me?game=Valorant")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    classification = data["data"]["classification"]
    assert "primary_role" in classification
    assert "confidence_score" in classification
    assert "reasoning" in classification


@pytest.mark.asyncio
async def test_ai_skill_profile_authenticated(authenticated_client: AsyncClient):
    """Test GET /skill-profile generates Six-Axis Skill Profile with 200 OK."""
    res = await authenticated_client.get("/skill-profile?game=Valorant")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    profile = data["data"]["skill_profile"]
    assert "mechanical_skill" in profile
    assert "communication" in profile
    assert "leadership" in profile
    assert "consistency" in profile
    assert "decision_making" in profile
    assert "game_sense" in profile
    assert "overall_score" in profile


@pytest.mark.asyncio
async def test_ai_compatibility_authenticated(authenticated_client: AsyncClient, mock_user: User):
    """Test GET /compatibility/{user_id} handles self-comparison and unknown targets."""
    # Self-comparison must raise 400 Bad Request
    self_res = await authenticated_client.get(f"/compatibility/{mock_user.id}")
    assert self_res.status_code == 400

    # Unknown target user raises 404
    random_id = uuid.uuid4()
    not_found_res = await authenticated_client.get(f"/compatibility/{random_id}")
    assert not_found_res.status_code == 404


@pytest.mark.asyncio
async def test_ai_recommendations_authenticated(authenticated_client: AsyncClient):
    """Test GET /recommendations returns Top 10 recommended teammates with 200 OK."""
    res = await authenticated_client.get("/recommendations?game=Valorant&limit=30")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    payload = data["data"]
    assert "top_teammates" in payload
    assert isinstance(payload["top_teammates"], list)
    assert len(payload["top_teammates"]) > 0


@pytest.mark.asyncio
async def test_ai_squad_authenticated(authenticated_client: AsyncClient):
    """Test GET /squad returns Best 5-player squad composition with 200 OK."""
    res = await authenticated_client.get("/squad?game=Valorant&limit=30")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    payload = data["data"]
    assert "squad" in payload
    assert len(payload["squad"]["members"]) == 5
    assert "overall_score" in payload["squad"]
    assert "missing_roles" in payload
    assert "confidence_score" in payload


@pytest.mark.asyncio
async def test_ai_explanation_authenticated(authenticated_client: AsyncClient, mock_user: User):
    """Test GET /explanation/{user_id} handles self-comparison and unknown targets."""
    # Self-comparison raises 400 Bad Request
    self_res = await authenticated_client.get(f"/explanation/{mock_user.id}")
    assert self_res.status_code == 400

    # Unknown target user raises 404
    random_id = uuid.uuid4()
    not_found_res = await authenticated_client.get(f"/explanation/{random_id}")
    assert not_found_res.status_code == 404


# ==============================================================================
# 3. AIService Unit Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_ai_service_unit_methods():
    """Unit tests verifying AIService methods with mocked sub-services."""
    mock_db = AsyncMock()
    mock_dna_service = AsyncMock()
    mock_role_service = AsyncMock()
    mock_skill_service = AsyncMock()
    mock_compat_service = AsyncMock()
    mock_squad_service = AsyncMock()
    mock_explanation_service = AsyncMock()

    user_id = uuid.uuid4()
    target_id = uuid.uuid4()

    # 1. DNA Mock
    mock_dna_service.get_gamer_dna_card.return_value = GamerDNACardResponse(
        username="pro_tester",
        profile=None,
        primary_role="Controller",
        secondary_role="Support",
        leadership_score=80,
        communication_score=85,
        strategy_score=90,
        aggression_score=60,
        teamwork_score=85,
        confidence_score=80,
        personality="The Tactical Flexible Player",
        strengths=["High tactical awareness"],
        weaknesses=["Passive in early skirmishes"],
        recommended_playstyle="Anchor site executes",
    )

    service = AIService(
        db=mock_db,
        dna_service=mock_dna_service,
        role_classifier_service=mock_role_service,
        skill_profile_service=mock_skill_service,
        compatibility_service=mock_compat_service,
        squad_service=mock_squad_service,
        explanation_service=mock_explanation_service,
    )

    user = User(id=user_id, username="pro_tester", email="tester@squadsync.gg")

    # Test get_my_dna
    dna_res = await service.get_my_dna(user=user)
    assert isinstance(dna_res, GamerDNAMeResponse)
    assert dna_res.dna.primary_role == "Controller"
    assert dna_res.dna.leadership_score == 80
