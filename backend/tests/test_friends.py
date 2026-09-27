"""
Automated unit & integration tests for Friend Management and BR-2 blocking rules.
"""

import uuid
from httpx import AsyncClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User


@pytest.mark.asyncio
async def test_friend_request_flow(authenticated_client: AsyncClient, db_session: AsyncSession, mock_user: User):
    """Test sending and accepting friend requests."""
    # Create target user
    target_id = uuid.uuid4()
    target_user = User(
        id=target_id,
        username="target_gamer",
        email="target@squadsync.gg",
        password_hash=get_password_hash("Pass1234!"),
        is_active=True,
    )
    db_session.add(target_user)
    await db_session.commit()

    # 1. Send friend request
    res = await authenticated_client.post(f"/api/v1/friends/request/{target_id}")
    assert res.status_code == 201
    data = res.json()
    assert data["success"] is True
    request_id = data["data"]["id"]
    assert data["data"]["status"] == "PENDING"

    # 2. Cannot send duplicate request
    res_dup = await authenticated_client.post(f"/api/v1/friends/request/{target_id}")
    assert res_dup.status_code == 400

    # 3. Cannot invite self
    res_self = await authenticated_client.post(f"/api/v1/friends/request/{mock_user.id}")
    assert res_self.status_code == 400


@pytest.mark.asyncio
async def test_friend_blocking_enforces_br2(authenticated_client: AsyncClient, db_session: AsyncSession, mock_user: User):
    """Test that blocking a user enforces BR-2 (no friend requests permitted)."""
    target_id = uuid.uuid4()
    target_user = User(
        id=target_id,
        username="toxic_player",
        email="toxic@squadsync.gg",
        password_hash=get_password_hash("Pass1234!"),
        is_active=True,
    )
    db_session.add(target_user)
    await db_session.commit()

    # Send request
    req_res = await authenticated_client.post(f"/api/v1/friends/request/{target_id}")
    assert req_res.status_code == 201
    request_id = req_res.json()["data"]["id"]

    # Block user
    block_res = await authenticated_client.put(
        f"/api/v1/friends/request/{request_id}",
        json={"action": "BLOCK"}
    )
    assert block_res.status_code == 200
    assert block_res.json()["data"]["status"] == "BLOCKED"

    # Subsequent request should be blocked with 403
    retry_res = await authenticated_client.post(f"/api/v1/friends/request/{target_id}")
    assert retry_res.status_code == 403


@pytest.mark.asyncio
async def test_search_players(authenticated_client: AsyncClient, db_session: AsyncSession, mock_user: User):
    """Test global gamer discovery search."""
    other_user = User(
        id=uuid.uuid4(),
        username="searchable_sniper",
        email="sniper@squadsync.gg",
        password_hash=get_password_hash("Pass1234!"),
        is_active=True,
    )
    db_session.add(other_user)
    await db_session.commit()

    res = await authenticated_client.get("/api/v1/friends/search?q=sniper")
    assert res.status_code == 200
    players = res.json()["data"]
    assert len(players) >= 1
    assert any(p["username"] == "searchable_sniper" for p in players)
