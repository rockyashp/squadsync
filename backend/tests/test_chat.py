"""
Automated unit & integration tests for Real-Time Chat & WebSockets (SRS 4.8 & NF-1.4).
"""

import uuid
from fastapi.testclient import TestClient
from httpx import AsyncClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.core.websocket_manager import ws_manager
from app.main import app
from app.models.team import Team, TeamMember
from app.models.user import User


@pytest.mark.asyncio
async def test_direct_chat_history_and_persistence(authenticated_client: AsyncClient, db_session: AsyncSession, mock_user: User):
    """Test saving and retrieving 1-on-1 direct chat history."""
    friend = User(
        id=uuid.uuid4(),
        username="chat_buddy",
        email="buddy@squadsync.gg",
        password_hash=get_password_hash("Pass1234!"),
        is_active=True,
    )
    db_session.add(friend)
    await db_session.commit()

    # Post message via ChatService
    from app.services.chat_service import ChatService
    service = ChatService(db_session)
    msg = await service.save_message(
        sender_id=mock_user.id,
        content="Hey buddy, ready for ranked?",
        recipient_id=friend.id,
    )
    assert msg.content == "Hey buddy, ready for ranked?"
    assert msg.sender_id == mock_user.id

    # Retrieve history via REST API
    res = await authenticated_client.get(f"/api/v1/chat/direct/{friend.id}")
    assert res.status_code == 200
    history = res.json()["data"]
    assert len(history) >= 1
    assert any("ready for ranked" in m["content"] for m in history)


@pytest.mark.asyncio
async def test_squad_chat_history_br3_isolation(authenticated_client: AsyncClient, db_session: AsyncSession, mock_user: User):
    """Test squad chat channel adheres to BR-3 membership boundary."""
    # 1. Team mock_user belongs to
    team = Team(
        id=uuid.uuid4(),
        name="Chat Squad",
        game="VALORANT",
        owner_id=mock_user.id,
    )
    db_session.add(team)
    db_session.add(TeamMember(team_id=team.id, user_id=mock_user.id, role="Captain"))
    await db_session.commit()

    from app.services.chat_service import ChatService
    service = ChatService(db_session)
    await service.save_message(
        sender_id=mock_user.id,
        content="Plant spike on A site!",
        team_id=team.id,
    )

    # Fetch history as squad member -> 200 OK
    res = await authenticated_client.get(f"/api/v1/chat/team/{team.id}")
    assert res.status_code == 200
    assert any("Plant spike" in m["content"] for m in res.json()["data"])

    # 2. Team mock_user does NOT belong to
    other_user = User(
        id=uuid.uuid4(),
        username="enemy_leader",
        email="enemy@squadsync.gg",
        password_hash=get_password_hash("Pass1234!"),
        is_active=True,
    )
    db_session.add(other_user)
    await db_session.commit()

    other_team = Team(
        id=uuid.uuid4(),
        name="Opponent Squad",
        game="VALORANT",
        owner_id=other_user.id,
    )
    db_session.add(other_team)
    await db_session.commit()

    forbidden_res = await authenticated_client.get(f"/api/v1/chat/team/{other_team.id}")
    assert forbidden_res.status_code == 403


def test_websocket_chat_auth_and_messaging():
    """Test WebSocket connection with JWT authentication and ping/pong."""
    client = TestClient(app)

    # 1. Missing / Invalid token -> Connection rejected
    with pytest.raises(Exception):
        with client.websocket_connect("/api/v1/chat/ws?token=invalid_token"):
            pass

    # 2. Valid token -> Connection accepted
    user_id = uuid.uuid4()
    valid_token = create_access_token(subject=str(user_id))

    with client.websocket_connect(f"/api/v1/chat/ws?token={valid_token}") as websocket:
        # Test ping / pong
        websocket.send_json({"type": "ping"})
        response = websocket.receive_json()
        assert response == {"type": "pong"}

        # Verify presence is ONLINE
        assert ws_manager.is_user_online(user_id) is True

    # Sockets closed -> verify presence updated
    assert ws_manager.is_user_online(user_id) is False
