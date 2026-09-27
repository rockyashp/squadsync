"""
Tests for Gamer Profile CRUD operations and input validation:
- Input validation (strings, avatar URLs)
- Authentication enforcement on all profile endpoints
- Profile retrieval, updates, and 404 responses
"""

import pytest
from httpx import AsyncClient

from app.schemas.profile import GamerProfileCreate, GamerProfileUpdate


def test_avatar_url_validation_rejections():
    """Verify avatar_url validator strictly rejects non-HTTP/HTTPS URLs."""
    with pytest.raises(ValueError) as exc_info:
        GamerProfileCreate(avatar_url="ftp://files.example.com/pic.png")
    assert "Avatar URL must be a valid HTTP or HTTPS address" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        GamerProfileCreate(avatar_url="javascript:alert(1)")
    assert "Avatar URL must be a valid HTTP or HTTPS address" in str(exc_info.value)


def test_avatar_url_valid():
    """Verify valid avatar HTTP and HTTPS URLs pass validation."""
    valid_https = GamerProfileCreate(avatar_url="https://cdn.squadsync.gg/avatars/user.jpg")
    assert valid_https.avatar_url == "https://cdn.squadsync.gg/avatars/user.jpg"

    valid_http = GamerProfileCreate(avatar_url="http://images.squadsync.gg/avatars/user.jpg")
    assert valid_http.avatar_url == "http://images.squadsync.gg/avatars/user.jpg"


def test_string_field_stripping():
    """Verify leading and trailing whitespaces are automatically stripped."""
    profile = GamerProfileCreate(
        full_name="   Alex Mercer   ",
        favorite_game="  Valorant  ",
        rank=" Immortal 1 ",
    )
    assert profile.full_name == "Alex Mercer"
    assert profile.favorite_game == "Valorant"
    assert profile.rank == "Immortal 1"


@pytest.mark.asyncio
async def test_get_profile_unauthenticated(client: AsyncClient):
    """Test GET /api/v1/profile/me returns 401 without Bearer token."""
    response = await client.get("/api/v1/profile/me")
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False


@pytest.mark.asyncio
async def test_create_profile_unauthenticated(client: AsyncClient):
    """Test POST /api/v1/profile returns 401 without Bearer token."""
    response = await client.post("/api/v1/profile", json={"full_name": "Test Player"})
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False


@pytest.mark.asyncio
async def test_update_profile_unauthenticated(client: AsyncClient):
    """Test PUT /api/v1/profile/me returns 401 without Bearer token."""
    response = await client.put("/api/v1/profile/me", json={"rank": "Radiant"})
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False


@pytest.mark.asyncio
async def test_get_profile_me_not_found(authenticated_client: AsyncClient):
    """Test GET /api/v1/profile/me returns 404 when profile does not exist."""
    response = await authenticated_client.get("/api/v1/profile/me")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "not found" in data["message"].lower()


@pytest.mark.asyncio
async def test_create_profile_invalid_avatar(authenticated_client: AsyncClient):
    """Test POST /api/v1/profile returns 422 when avatar URL is invalid protocol."""
    payload = {
        "full_name": "Alex Mercer",
        "avatar_url": "ftp://malicious.com/exploit.png",
    }
    response = await authenticated_client.post("/api/v1/profile", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert any("avatar" in err.get("field", "") for err in data["errors"])


def test_gamer_profile_schema_new_fields_and_aliases():
    """Test GamerProfileCreate synchronizes new fields and legacy aliases properly."""
    from app.schemas.profile import GamerProfileCreate

    payload = {
        "display_name": "  GhostOperator  ",
        "bio": "Tactical FPS anchor.",
        "region": "  EU-West  ",
        "language": "English",
        "preferred_games": ["Valorant", "Valorant", "CS2"],
        "preferred_roles": ["Sentinel", "Controller", "Sentinel"],
        "availability": "Weekends all day",
        "avatar": "https://cdn.squadsync.gg/avatars/ghost.png",
    }
    profile = GamerProfileCreate(**payload)
    assert profile.display_name == "GhostOperator"
    assert profile.full_name == "GhostOperator"
    assert profile.region == "EU-West"
    assert profile.preferred_games == ["Valorant", "CS2"]
    assert profile.preferred_roles == ["Sentinel", "Controller"]
    assert profile.avatar == "https://cdn.squadsync.gg/avatars/ghost.png"
    assert profile.avatar_url == "https://cdn.squadsync.gg/avatars/ghost.png"
    assert profile.availability == "Weekends all day"
    assert profile.gaming_schedule == "Weekends all day"
