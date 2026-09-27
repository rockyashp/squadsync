"""
Tests for Gamer DNA Card:
- Strengths and Weaknesses derivation logic
- Recommended Playstyle synthesis
- GET /dna/me endpoint contract
- Unified ApiResponse envelope compliance
"""

import uuid
import pytest
from httpx import AsyncClient

from app.models.gamer_dna import GamerDNA
from app.services.dna_service import DNAService


def test_dna_strengths_derivation():
    """Verify that strengths are calculated dynamically based on high scores (>=70) and role defaults."""
    dna_service = DNAService(db=None)  # type: ignore[arg-type]
    uid = uuid.uuid4()

    dna = GamerDNA(
        user_id=uid,
        leadership=85,
        communication=90,
        strategy=50,
        teamwork=40,
        aggression=60,
        primary_role="Leader",
        secondary_role="Support",
        personality="The Inspirational Captain",
    )

    strengths = dna_service._calculate_strengths(dna)
    assert len(strengths) >= 3
    assert any("shotcaller" in s.lower() for s in strengths)
    assert any("callout" in s.lower() for s in strengths)


def test_dna_weaknesses_derivation():
    """Verify that weaknesses are generated constructively for low-scoring traits (<=45)."""
    dna_service = DNAService(db=None)  # type: ignore[arg-type]
    uid = uuid.uuid4()

    dna = GamerDNA(
        user_id=uid,
        leadership=90,
        communication=85,
        strategy=40,
        teamwork=35,
        aggression=75,
        primary_role="Duelist",
        secondary_role="Leader",
        personality="The Aggressive Warlord",
    )

    weaknesses = dna_service._calculate_weaknesses(dna)
    assert len(weaknesses) >= 2
    assert any("tunnel" in w.lower() or "cooldown" in w.lower() for w in weaknesses)
    assert any("solo" in w.lower() or "trade" in w.lower() for w in weaknesses)


def test_dna_recommended_playstyle():
    """Verify playstyle advice combines roles and personality into actionable guidance."""
    dna_service = DNAService(db=None)  # type: ignore[arg-type]
    uid = uuid.uuid4()

    dna = GamerDNA(
        user_id=uid,
        leadership=90,
        communication=85,
        strategy=85,
        teamwork=70,
        aggression=50,
        primary_role="Leader",
        secondary_role="Strategist",
        personality="The Grandmaster Shotcaller",
    )

    playstyle = dna_service._calculate_playstyle(dna)
    assert "In-Game Leader" in playstyle
    assert "default" in playstyle.lower()
    assert "synchronized" in playstyle.lower()


@pytest.mark.asyncio
async def test_get_dna_me_unauthenticated(client: AsyncClient):
    """Test GET /api/v1/dna/me requires authentication (401 Unauthorized)."""
    response = await client.get("/api/v1/dna/me")
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert "token" in data["message"].lower() or "authenticated" in data["message"].lower() or "credentials" in data["message"].lower()


@pytest.mark.asyncio
async def test_get_dna_me_not_found(authenticated_client: AsyncClient):
    """Test GET /api/v1/dna/me returns 404 Not Found when Gamer DNA is not yet generated."""
    response = await authenticated_client.get("/api/v1/dna/me")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "not found" in data["message"].lower() or "survey" in data["message"].lower()
