"""
Friendship Service implementing social connectivity, friend requests, and blocking rules (BR-2).
"""

import uuid
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.friendship import Friendship, FriendshipStatus
from app.models.gamer_profile import GamerProfile
from app.models.user import User
from app.schemas.friendship import FriendGamerItem, FriendshipResponse, PlayerSearchResult


class FriendshipService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def send_request(self, requester_id: uuid.UUID, addressee_id: uuid.UUID) -> FriendshipResponse:
        """Sends a friend request while enforcing BR-2 (no requests between blocked accounts)."""
        if requester_id == addressee_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot send a friend request to yourself."
            )

        # Verify addressee exists
        target_user = await self.db.get(User, addressee_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target player not found."
            )

        # Check existing relationship in either direction
        stmt = select(Friendship).where(
            or_(
                (Friendship.requester_id == requester_id) & (Friendship.addressee_id == addressee_id),
                (Friendship.requester_id == addressee_id) & (Friendship.addressee_id == requester_id),
            )
        )
        res = await self.db.execute(stmt)
        existing = res.scalar_one_or_none()

        if existing:
            if existing.status == FriendshipStatus.BLOCKED.value:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot send friend request: account communication is restricted."
                )
            if existing.status == FriendshipStatus.ACCEPTED.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You are already friends with this player."
                )
            if existing.status == FriendshipStatus.PENDING.value:
                if existing.requester_id == requester_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Friend request has already been sent and is pending."
                    )
                else:
                    # Target has already invited current user -> auto-accept
                    existing.status = FriendshipStatus.ACCEPTED.value
                    await self.db.commit()
                    await self.db.refresh(existing)
                    return FriendshipResponse.model_validate(existing)

        # Create new friend request
        friendship = Friendship(
            requester_id=requester_id,
            addressee_id=addressee_id,
            status=FriendshipStatus.PENDING.value,
        )
        self.db.add(friendship)
        await self.db.commit()
        await self.db.refresh(friendship)
        return FriendshipResponse.model_validate(friendship)

    async def respond_to_request(self, request_id: uuid.UUID, current_user_id: uuid.UUID, action: str) -> FriendshipResponse:
        """Accepts, rejects, or blocks a friend request."""
        friendship = await self.db.get(Friendship, request_id)
        if not friendship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Friend request record not found."
            )

        action_upper = action.upper()
        if action_upper == "BLOCK":
            # Either party can block
            if friendship.requester_id != current_user_id and friendship.addressee_id != current_user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized.")
            friendship.status = FriendshipStatus.BLOCKED.value
        elif action_upper == "ACCEPT":
            if friendship.addressee_id != current_user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the recipient can accept this invitation.")
            friendship.status = FriendshipStatus.ACCEPTED.value
        elif action_upper == "REJECT":
            if friendship.addressee_id != current_user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the recipient can reject this invitation.")
            friendship.status = FriendshipStatus.REJECTED.value
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid action: {action}")

        await self.db.commit()
        await self.db.refresh(friendship)
        return FriendshipResponse.model_validate(friendship)

    async def get_friends_list(self, user_id: uuid.UUID) -> list[FriendGamerItem]:
        """Returns all confirmed active friends with gamer profiles."""
        stmt = select(Friendship).where(
            (Friendship.status == FriendshipStatus.ACCEPTED.value) &
            or_(Friendship.requester_id == user_id, Friendship.addressee_id == user_id)
        ).options(
            selectinload(Friendship.requester).selectinload(User.profile),
            selectinload(Friendship.addressee).selectinload(User.profile),
        )
        result = await self.db.execute(stmt)
        friendships = result.scalars().all()

        items: list[FriendGamerItem] = []
        for f in friendships:
            friend_user = f.addressee if f.requester_id == user_id else f.requester
            prof = friend_user.profile if friend_user else None
            items.append(
                FriendGamerItem(
                    friendship_id=f.id,
                    user_id=friend_user.id,
                    username=friend_user.username,
                    gamer_tag=prof.gamer_tag if prof else friend_user.username,
                    avatar_url=prof.avatar_url if prof else None,
                    primary_role=prof.primary_role if prof else None,
                    rank_tier=prof.rank_tier if prof else None,
                    is_online=True,
                    direction="friend",
                )
            )
        return items

    async def get_pending_requests(self, user_id: uuid.UUID) -> list[FriendGamerItem]:
        """Returns incoming pending requests waiting for user's response."""
        stmt = select(Friendship).where(
            (Friendship.status == FriendshipStatus.PENDING.value) &
            (Friendship.addressee_id == user_id)
        ).options(
            selectinload(Friendship.requester).selectinload(User.profile),
        )
        result = await self.db.execute(stmt)
        incoming = result.scalars().all()

        items: list[FriendGamerItem] = []
        for f in incoming:
            sender = f.requester
            prof = sender.profile if sender else None
            items.append(
                FriendGamerItem(
                    friendship_id=f.id,
                    user_id=sender.id,
                    username=sender.username,
                    gamer_tag=prof.gamer_tag if prof else sender.username,
                    avatar_url=prof.avatar_url if prof else None,
                    primary_role=prof.primary_role if prof else None,
                    rank_tier=prof.rank_tier if prof else None,
                    is_online=True,
                    direction="incoming",
                )
            )
        return items

    async def remove_friend(self, user_id: uuid.UUID, friend_user_id: uuid.UUID) -> bool:
        """Removes friendship connection."""
        stmt = select(Friendship).where(
            or_(
                (Friendship.requester_id == user_id) & (Friendship.addressee_id == friend_user_id),
                (Friendship.requester_id == friend_user_id) & (Friendship.addressee_id == user_id),
            )
        )
        res = await self.db.execute(stmt)
        record = res.scalar_one_or_none()
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Friendship not found.")
        await self.db.delete(record)
        await self.db.commit()
        return True

    async def search_players(self, current_user_id: uuid.UUID, query: str) -> list[PlayerSearchResult]:
        """Global search for players with relationship status."""
        clean_q = f"%{query.strip().lower()}%"
        stmt = select(User).join(GamerProfile, User.id == GamerProfile.user_id, isouter=True).where(
            User.id != current_user_id,
            or_(
                User.username.ilike(clean_q),
                User.email.ilike(clean_q),
                GamerProfile.display_name.ilike(clean_q)
            )
        ).options(selectinload(User.profile)).limit(20)

        result = await self.db.execute(stmt)
        users = result.scalars().all()

        results: list[PlayerSearchResult] = []
        for u in users:
            # Check relationship status with current user
            f_stmt = select(Friendship).where(
                or_(
                    (Friendship.requester_id == current_user_id) & (Friendship.addressee_id == u.id),
                    (Friendship.requester_id == u.id) & (Friendship.addressee_id == current_user_id),
                )
            )
            f_res = await self.db.execute(f_stmt)
            f_rel = f_res.scalar_one_or_none()

            rel_status = None
            if f_rel:
                if f_rel.status == FriendshipStatus.ACCEPTED.value:
                    rel_status = "ACCEPTED"
                elif f_rel.status == FriendshipStatus.BLOCKED.value:
                    rel_status = "BLOCKED"
                elif f_rel.status == FriendshipStatus.PENDING.value:
                    rel_status = "PENDING_SENT" if f_rel.requester_id == current_user_id else "PENDING_RECEIVED"

            prof = u.profile
            results.append(
                PlayerSearchResult(
                    user_id=u.id,
                    username=u.username,
                    gamer_tag=prof.gamer_tag if prof else u.username,
                    avatar_url=prof.avatar_url if prof else None,
                    primary_role=prof.primary_role if prof else None,
                    rank_tier=prof.rank_tier if prof else None,
                    friendship_status=rel_status,
                )
            )
        return results
