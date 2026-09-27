"""
CandidateRepository for querying and assembling matchmaking candidate profiles.
Performs optimized asynchronous queries joining User, GamerProfile, GamerDNA, and PlayerStat.
"""

from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any
import uuid

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.matchmaking.rank_scaler import normalize_rank_to_mmr
from app.models.gamer_dna import GamerDNA
from app.models.gamer_profile import GamerProfile
from app.models.player_stat import PlayerStat
from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.matchmaking import MatchmakingCandidate


class CandidateRepository(BaseRepository[User]):
    """
    Repository specializing in querying candidate player profiles for matchmaking and squad recommendations.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(User, db)

    async def get_candidate_pool(
        self,
        exclude_user_id: uuid.UUID,
        target_game: str = "Valorant",
        target_region: str | None = None,
        limit: int = 40,
    ) -> list[MatchmakingCandidate]:
        """
        Queries active users, gathers their DNA, profile preferences, and competitive stats,
        and constructs normalized MatchmakingCandidate instances.
        """
        # 1. Query active users excluding the requesting user
        conditions = [User.id != exclude_user_id, User.is_active == True]
        stmt = select(User).where(and_(*conditions)).limit(limit)
        result = await self.db.execute(stmt)
        users = result.scalars().all()

        candidates: list[MatchmakingCandidate] = []
        for u in users:
            if not isinstance(u, User):
                continue
            cand = await self.build_candidate_for_user(u, target_game=target_game)
            if target_region and cand.region.lower() != target_region.lower():
                continue
            candidates.append(cand)

        return candidates

    async def build_candidate_for_user(
        self,
        user: User,
        target_game: str = "Valorant",
    ) -> MatchmakingCandidate:
        """Hydrates a single User entity into a normalized MatchmakingCandidate."""
        user_id = user.id

        # 1. Profile
        stmt_prof = select(GamerProfile).where(GamerProfile.user_id == user_id)
        res_prof = await self.db.execute(stmt_prof)
        profile = res_prof.scalar_one_or_none()

        # 2. DNA
        stmt_dna = select(GamerDNA).where(GamerDNA.user_id == user_id)
        res_dna = await self.db.execute(stmt_dna)
        dna = res_dna.scalar_one_or_none()

        # 3. Stats
        stmt_stat = (
            select(PlayerStat)
            .where(PlayerStat.user_id == user_id)
            .order_by(PlayerStat.matches_played.desc())
        )
        res_stat = await self.db.execute(stmt_stat)
        stat = res_stat.scalars().first()

        # Extract fields with safe defaults
        username = (
            user.username
            if (isinstance(getattr(user, "username", None), str) and user.username)
            else f"player_{str(user_id)[:8]}"
        )
        display_name = (
            profile.display_name
            if (isinstance(profile, GamerProfile) and profile.display_name)
            else username
        )
        avatar_url = (
            profile.avatar
            if (isinstance(profile, GamerProfile) and profile.avatar)
            else None
        )

        # Stats
        if isinstance(stat, PlayerStat):
            rank = stat.current_rank or "Gold 1"
            rank_rating = int(stat.rank_rating) if stat.rank_rating is not None else 50
            win_rate = float(stat.win_rate) if stat.win_rate is not None else 50.0
            matches_played = int(stat.matches_played) if stat.matches_played is not None else 20
            kd_ratio = float(stat.kd_ratio) if stat.kd_ratio is not None else 1.0
        else:
            rank = "Gold 1"
            rank_rating = 50
            win_rate = 50.0
            matches_played = 20
            kd_ratio = 1.0

        mmr = normalize_rank_to_mmr(rank, rank_rating)

        # DNA Traits
        if isinstance(dna, GamerDNA):
            leadership = int(dna.leadership) if dna.leadership is not None else 50
            communication = int(dna.communication) if dna.communication is not None else 50
            strategy = int(dna.strategy) if dna.strategy is not None else 50
            teamwork = int(dna.teamwork) if dna.teamwork is not None else 50
            aggression = int(dna.aggression) if dna.aggression is not None else 50
            confidence = int(getattr(dna, "confidence", 50) or 50)
            primary_role = dna.primary_role or "Support"
            secondary_role = dna.secondary_role
            personality = dna.personality or "The Tactical Flexible Player"
        else:
            leadership = 50
            communication = 50
            strategy = 50
            teamwork = 50
            aggression = 50
            confidence = 50
            primary_role = "Support"
            secondary_role = None
            personality = "The Tactical Flexible Player"

        # Logistics
        if isinstance(profile, GamerProfile):
            region = profile.region or "NA-East"
            languages = [profile.language] if profile.language else ["en"]
            preferred_games = profile.preferred_games or [target_game]
            preferred_roles = profile.preferred_roles or [primary_role]
        else:
            region = "NA-East"
            languages = ["en"]
            preferred_games = [target_game]
            preferred_roles = [primary_role]

        schedule_tags = ["evenings"]

        return MatchmakingCandidate(
            user_id=user_id,
            username=username,
            display_name=display_name,
            avatar_url=avatar_url,
            rank=rank,
            mmr=mmr,
            win_rate=win_rate,
            matches_played=matches_played,
            kd_ratio=kd_ratio,
            leadership=leadership,
            communication=communication,
            strategy=strategy,
            teamwork=teamwork,
            aggression=aggression,
            confidence=confidence,
            primary_role=primary_role,
            secondary_role=secondary_role,
            personality=personality,
            role_affinities={},
            region=region,
            languages=languages,
            schedule_tags=schedule_tags,
            preferred_games=preferred_games,
            preferred_roles=preferred_roles,
        )
