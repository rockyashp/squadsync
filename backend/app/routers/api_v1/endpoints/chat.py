"""
Real-Time Chat & WebSocket API endpoints.
Provides instant messaging (<1s latency per NF-1.4), presence tracking, and persistent chat logs.
"""

import logging
import uuid
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
import jwt
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.dependencies import CurrentUser, DatabaseSession
from app.core.security import decode_token
from app.core.websocket_manager import ws_manager
from app.models.team import TeamMember
from app.schemas.chat import ChatMessageResponse, MarkReadRequest
from app.schemas.common import ApiResponse
from app.services.chat_service import ChatService

logger = logging.getLogger("squadsync.chat")
router = APIRouter()


@router.websocket("/ws")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT Bearer token for authentication"),
):
    """
    Authenticated WebSocket endpoint for real-time bi-directional messaging.
    Enforces JWT security (NF-3.1) and delivers sub-second message delivery (NF-1.4).
    """
    # 1. Authenticate JWT token
    try:
        payload = decode_token(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        user_id = uuid.UUID(user_id_str)
    except (jwt.PyJWTError, ValueError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # 2. Register socket connection
    await ws_manager.connect(websocket, user_id)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "direct_message")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            async with AsyncSessionLocal() as session:
                service = ChatService(session)

                if msg_type == "direct_message":
                    recipient_id_str = data.get("recipient_id")
                    content = data.get("content", "")
                    if recipient_id_str and content:
                        recip_id = uuid.UUID(recipient_id_str)
                        saved_msg = await service.save_message(
                            sender_id=user_id,
                            content=content,
                            recipient_id=recip_id,
                        )
                        event = {
                            "type": "new_direct_message",
                            "data": saved_msg.model_dump(mode="json"),
                        }
                        # Deliver to recipient
                        await ws_manager.send_direct_message(event, recip_id)
                        # Echo back to sender's active sockets
                        await ws_manager.send_direct_message(event, user_id)

                elif msg_type == "team_message":
                    team_id_str = data.get("team_id")
                    content = data.get("content", "")
                    if team_id_str and content:
                        t_id = uuid.UUID(team_id_str)
                        saved_msg = await service.save_message(
                            sender_id=user_id,
                            content=content,
                            team_id=t_id,
                        )
                        # Fetch all squad members
                        m_stmt = select(TeamMember.user_id).where(TeamMember.team_id == t_id)
                        m_res = await session.execute(m_stmt)
                        member_ids = m_res.scalars().all()

                        event = {
                            "type": "new_team_message",
                            "data": saved_msg.model_dump(mode="json"),
                        }
                        await ws_manager.broadcast_to_users(event, member_ids)

                elif msg_type == "typing":
                    # Forward typing indicator to recipient or squad
                    recip_str = data.get("recipient_id")
                    if recip_str:
                        recip_id = uuid.UUID(recip_str)
                        await ws_manager.send_direct_message(
                            {"type": "user_typing", "sender_id": str(user_id)},
                            recip_id,
                        )

    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.warning("Error in WebSocket session for user %s: %s", user_id, e)
        await ws_manager.disconnect(websocket, user_id)


@router.get(
    "/direct/{other_user_id}",
    response_model=ApiResponse[list[ChatMessageResponse]],
    summary="Get 1-on-1 Chat History",
    description="Fetches chronological direct message history between authenticated user and another player.",
)
async def get_direct_history(
    other_user_id: uuid.UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
    limit: int = Query(50, ge=1, le=200),
):
    service = ChatService(db)
    messages = await service.get_direct_history(
        user_a_id=current_user.id,
        user_b_id=other_user_id,
        limit=limit,
    )
    return ApiResponse.ok(data=messages, message=f"Retrieved {len(messages)} messages.")


@router.get(
    "/team/{team_id}",
    response_model=ApiResponse[list[ChatMessageResponse]],
    summary="Get Squad Channel Chat History",
    description="Fetches squad channel chat logs. Enforces BR-3 (restricted strictly to squad members).",
)
async def get_team_history(
    team_id: uuid.UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
    limit: int = Query(50, ge=1, le=200),
):
    service = ChatService(db)
    messages = await service.get_team_history(
        team_id=team_id,
        current_user_id=current_user.id,
        limit=limit,
    )
    return ApiResponse.ok(data=messages, message=f"Retrieved {len(messages)} squad messages.")


@router.post(
    "/read",
    response_model=ApiResponse[int],
    summary="Mark Messages Read",
    description="Marks direct or team channel messages as read.",
)
async def mark_messages_read(
    payload: MarkReadRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
):
    service = ChatService(db)
    count = await service.mark_read(
        user_id=current_user.id,
        sender_id=payload.sender_id,
        team_id=payload.team_id,
    )
    return ApiResponse.ok(data=count, message=f"Marked {count} messages as read.")


@router.get(
    "/presence/{target_user_id}",
    response_model=ApiResponse[dict],
    summary="Check Player Online Status",
    description="Checks if a player currently has an active WebSocket session.",
)
async def check_player_presence(
    target_user_id: uuid.UUID,
    current_user: CurrentUser,
):
    online = ws_manager.is_user_online(target_user_id)
    return ApiResponse.ok(
        data={"user_id": target_user_id, "is_online": online},
        message="Presence status retrieved.",
    )
