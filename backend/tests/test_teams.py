"""
Automated unit & integration tests for Team/Squad Management and BR-3 isolation.
"""

import uuid
from httpx import AsyncClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User


@pytest.mark.asyncio
async def test_team_creation_and_roster(authenticated_client: AsyncClient, db_session: AsyncSession, mock_user: User):
    """Test squad creation and initial roster validation."""
    payload = {
        "name": "Alpha Strike",
        "game": "VALORANT",
        "description": "Immortal push squad",
        "synergy_score": 92.5,
        "member_ids": [],
        "member_roles": {str(mock_user.id): "Duelist"},
    }

    res = await authenticated_client.post("/api/v1/teams", json=payload)
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["name"] == "Alpha Strike"
    assert data["game"] == "VALORANT"
    assert data["owner_id"] == str(mock_user.id)
    assert len(data["members"]) == 1
    assert data["members"][0]["user_id"] == str(mock_user.id)
    assert data["members"][0]["role"] == "Duelist"


@pytest.mark.asyncio
async def test_team_dashboard_access_isolation_br3(authenticated_client: AsyncClient, db_session: AsyncSession, mock_user: User):
    """Test BR-3: non-members cannot access squad dashboard."""
    # Create an external team owned by someone else
    other_owner = User(
        id=uuid.uuid4(),
        username="other_leader",
        email="leader@squadsync.gg",
        password_hash=get_password_hash("Pass1234!"),
        is_active=True,
    )
    db_session.add(other_owner)
    await db_session.commit()

    from app.models.team import Team, TeamMember
    secret_team = Team(
        id=uuid.uuid4(),
        name="Secret Squad",
        game="CS2",
        owner_id=other_owner.id,
        synergy_score=80.0,
    )
    db_session.add(secret_team)
    db_session.add(TeamMember(team_id=secret_team.id, user_id=other_owner.id, role="Captain"))
    await db_session.commit()

    # Authenticated user is NOT in secret_team -> must be 403 Forbidden
    res = await authenticated_client.get(f"/api/v1/teams/{secret_team.id}")
    assert res.status_code == 403
    assert "not a member" in res.json().get("message", res.json().get("detail", "")).lower()


@pytest.mark.asyncio
async def test_team_invite_and_remove(authenticated_client: AsyncClient, db_session: AsyncSession, mock_user: User):
    """Test inviting a member and removing a member."""
    # 1. Create team
    create_res = await authenticated_client.post("/api/v1/teams", json={
        "name": "Delta Force",
        "game": "Apex Legends",
    })
    assert create_res.status_code == 201
    team_id = create_res.json()["data"]["id"]

    # 2. Create player to invite
    recruit = User(
        id=uuid.uuid4(),
        username="recruit_player",
        email="recruit@squadsync.gg",
        password_hash=get_password_hash("Pass1234!"),
        is_active=True,
    )
    db_session.add(recruit)
    await db_session.commit()

    # 3. Invite member
    inv_res = await authenticated_client.post(
        f"/api/v1/teams/{team_id}/invite",
        json={"user_id": str(recruit.id), "role": "Recon"}
    )
    assert inv_res.status_code == 200
    roster = inv_res.json()["data"]["members"]
    assert len(roster) == 2
    assert any(m["user_id"] == str(recruit.id) and m["role"] == "Recon" for m in roster)

    # 4. Remove member
    del_res = await authenticated_client.delete(f"/api/v1/teams/{team_id}/members/{recruit.id}")
    assert del_res.status_code == 200
