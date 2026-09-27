"""
Team & Squad Service implementing team creation, roster management, and BR-3 isolation.
"""

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.gamer_profile import GamerProfile
from app.models.team import Team, TeamMember
from app.models.user import User
from app.schemas.team import TeamCreate, TeamInviteRequest, TeamMemberResponse, TeamResponse


class TeamService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_team(self, owner: User, payload: TeamCreate) -> TeamResponse:
        """Creates a persistent squad and initializes owner and teammates into the roster."""
        team = Team(
            name=payload.name,
            game=payload.game,
            owner_id=owner.id,
            description=payload.description,
            synergy_score=payload.synergy_score,
            max_members=5,
        )
        self.db.add(team)
        await self.db.flush()

        # Add owner as first team member
        owner_role = payload.member_roles.get(str(owner.id), "Captain")
        owner_member = TeamMember(
            team_id=team.id,
            user_id=owner.id,
            role=owner_role,
        )
        self.db.add(owner_member)

        # Add other initial squad members if provided
        for mem_id in payload.member_ids:
            if mem_id != owner.id:
                mem_role = payload.member_roles.get(str(mem_id), "Flex")
                self.db.add(TeamMember(team_id=team.id, user_id=mem_id, role=mem_role))

        await self.db.commit()
        return await self.get_team(team.id, owner.id, bypass_member_check=True)

    async def get_team(self, team_id: uuid.UUID, current_user_id: uuid.UUID, bypass_member_check: bool = False) -> TeamResponse:
        """Retrieves squad details while enforcing BR-3 (squad dashboard access limited to members)."""
        stmt = select(Team).where(Team.id == team_id).options(
            selectinload(Team.owner),
            selectinload(Team.members).selectinload(TeamMember.user).selectinload(User.profile),
        )
        res = await self.db.execute(stmt)
        team = res.scalar_one_or_none()

        if not team:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Squad not found.")

        # Check membership (BR-3)
        member_ids = {m.user_id for m in team.members}
        if not bypass_member_check and current_user_id not in member_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access restricted: you are not a member of this squad."
            )

        member_responses = []
        for m in team.members:
            u = m.user
            prof = u.profile if u else None
            member_responses.append(
                TeamMemberResponse(
                    user_id=m.user_id,
                    username=u.username if u else "Player",
                    gamer_tag=prof.gamer_tag if prof else (u.username if u else None),
                    avatar_url=prof.avatar_url if prof else None,
                    role=m.role,
                    joined_at=m.created_at,
                )
            )

        return TeamResponse(
            id=team.id,
            name=team.name,
            game=team.game,
            owner_id=team.owner_id,
            owner_username=team.owner.username if team.owner else None,
            description=team.description,
            synergy_score=team.synergy_score,
            max_members=team.max_members,
            members=member_responses,
            created_at=team.created_at,
        )

    async def get_my_teams(self, user_id: uuid.UUID) -> list[TeamResponse]:
        """Lists all squads the user currently belongs to."""
        stmt = select(TeamMember.team_id).where(TeamMember.user_id == user_id)
        res = await self.db.execute(stmt)
        team_ids = res.scalars().all()

        teams = []
        for tid in team_ids:
            try:
                t = await self.get_team(tid, user_id, bypass_member_check=True)
                teams.append(t)
            except Exception:
                continue
        return teams

    async def add_member(self, team_id: uuid.UUID, current_user_id: uuid.UUID, invite: TeamInviteRequest) -> TeamResponse:
        """Invites a player into the team."""
        team = await self.db.get(Team, team_id)
        if not team:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Squad not found.")

        # Check existing members
        stmt = select(TeamMember).where(TeamMember.team_id == team_id)
        res = await self.db.execute(stmt)
        members = res.scalars().all()

        if len(members) >= team.max_members:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Squad roster is already full (max 5 players).")

        if any(m.user_id == invite.user_id for m in members):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Player is already in this squad.")

        new_member = TeamMember(
            team_id=team_id,
            user_id=invite.user_id,
            role=invite.role,
        )
        self.db.add(new_member)
        await self.db.commit()
        self.db.expire_all()
        return await self.get_team(team_id, current_user_id, bypass_member_check=True)

    async def remove_member(self, team_id: uuid.UUID, current_user_id: uuid.UUID, target_user_id: uuid.UUID) -> bool:
        """Removes a member from squad (owner or self-removal)."""
        team = await self.db.get(Team, team_id)
        if not team:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Squad not found.")

        if current_user_id != team.owner_id and current_user_id != target_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the squad leader can remove other members.")

        stmt = select(TeamMember).where((TeamMember.team_id == team_id) & (TeamMember.user_id == target_user_id))
        res = await self.db.execute(stmt)
        member = res.scalar_one_or_none()
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found in this squad.")

        await self.db.delete(member)
        await self.db.commit()
        return True
