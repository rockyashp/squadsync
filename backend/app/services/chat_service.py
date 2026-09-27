"""
Chat Service implementing message persistence, history retrieval, and BR-2/BR-3 access boundaries.
"""

from datetime import datetime, timezone
import html
import uuid
from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.chat import ChatMessage
from app.models.friendship import Friendship, FriendshipStatus
from app.models.team import Team, TeamMember
from app.models.user import User
from app.schemas.chat import ChatMessageResponse


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_message(
        self,
        sender_id: uuid.UUID,
        content: str,
        recipient_id: uuid.UUID | None = None,
        team_id: uuid.UUID | None = None,
    ) -> ChatMessageResponse:
        """Persists a chat message after validating boundaries (BR-2 block check, BR-3 team membership)."""
        clean_content = html.escape(content.strip())
        if not clean_content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message content cannot be empty.")

        if not recipient_id and not team_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Must specify either recipient_id or team_id.")

        # 1. Direct message boundary check (BR-2: no communication with blocked players)
        if recipient_id:
            if sender_id == recipient_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot send message to yourself.")

            f_stmt = select(Friendship).where(
                or_(
                    (Friendship.requester_id == sender_id) & (Friendship.addressee_id == recipient_id),
                    (Friendship.requester_id == recipient_id) & (Friendship.addressee_id == sender_id),
                )
            )
            f_res = await self.db.execute(f_stmt)
            rel = f_res.scalar_one_or_none()
            if rel and rel.status == FriendshipStatus.BLOCKED.value:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot send message: player communication is restricted."
                )

        # 2. Team message boundary check (BR-3: must be squad member)
        if team_id:
            m_stmt = select(TeamMember).where(
                (TeamMember.team_id == team_id) & (TeamMember.user_id == sender_id)
            )
            m_res = await self.db.execute(m_stmt)
            if not m_res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot post to team channel: you are not a member of this squad."
                )

        # Persist message
        msg = ChatMessage(
            sender_id=sender_id,
            recipient_id=recipient_id,
            team_id=team_id,
            content=clean_content,
            is_read=False,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)

        # Retrieve sender username
        sender = await self.db.get(User, sender_id)
        return ChatMessageResponse(
            id=msg.id,
            sender_id=msg.sender_id,
            sender_username=sender.username if sender else "Gamer",
            recipient_id=msg.recipient_id,
            team_id=msg.team_id,
            content=msg.content,
            is_read=msg.is_read,
            created_at=msg.created_at,
        )

    async def get_direct_history(
        self,
        user_a_id: uuid.UUID,
        user_b_id: uuid.UUID,
        limit: int = 50,
    ) -> list[ChatMessageResponse]:
        """Retrieves chronological 1-on-1 chat history between two gamers."""
        stmt = select(ChatMessage).where(
            or_(
                (ChatMessage.sender_id == user_a_id) & (ChatMessage.recipient_id == user_b_id),
                (ChatMessage.sender_id == user_b_id) & (ChatMessage.recipient_id == user_a_id),
            )
        ).options(selectinload(ChatMessage.sender)).order_by(ChatMessage.created_at.asc()).limit(limit)

        res = await self.db.execute(stmt)
        messages = res.scalars().all()

        return [
            ChatMessageResponse(
                id=m.id,
                sender_id=m.sender_id,
                sender_username=m.sender.username if m.sender else None,
                recipient_id=m.recipient_id,
                team_id=m.team_id,
                content=m.content,
                is_read=m.is_read,
                created_at=m.created_at,
            )
            for m in messages
        ]

    async def get_team_history(
        self,
        team_id: uuid.UUID,
        current_user_id: uuid.UUID,
        limit: int = 50,
    ) -> list[ChatMessageResponse]:
        """Retrieves squad channel history while enforcing BR-3 membership check."""
        m_stmt = select(TeamMember).where(
            (TeamMember.team_id == team_id) & (TeamMember.user_id == current_user_id)
        )
        m_res = await self.db.execute(m_stmt)
        if not m_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access restricted: you are not a member of this squad."
            )

        stmt = select(ChatMessage).where(
            ChatMessage.team_id == team_id
        ).options(selectinload(ChatMessage.sender)).order_by(ChatMessage.created_at.asc()).limit(limit)

        res = await self.db.execute(stmt)
        messages = res.scalars().all()

        return [
            ChatMessageResponse(
                id=m.id,
                sender_id=m.sender_id,
                sender_username=m.sender.username if m.sender else None,
                recipient_id=m.recipient_id,
                team_id=m.team_id,
                content=m.content,
                is_read=m.is_read,
                created_at=m.created_at,
            )
            for m in messages
        ]

    async def mark_read(
        self,
        user_id: uuid.UUID,
        sender_id: uuid.UUID | None = None,
        team_id: uuid.UUID | None = None,
    ) -> int:
        """Marks incoming messages as read."""
        if sender_id:
            stmt = update(ChatMessage).where(
                (ChatMessage.recipient_id == user_id) & (ChatMessage.sender_id == sender_id)
            ).values(is_read=True)
            res = await self.db.execute(stmt)
            await self.db.commit()
            return res.rowcount
        elif team_id:
            stmt = update(ChatMessage).where(
                (ChatMessage.team_id == team_id) & (ChatMessage.sender_id != user_id)
            ).values(is_read=True)
            res = await self.db.execute(stmt)
            await self.db.commit()
            return res.rowcount
        return 0
