"""
AI Compatibility Service orchestrating pairwise player comparisons.
Hydrates user profiles, psychometrics, and telemetry from the database,
and interfaces with the AICompatibilityEngine.
"""

from typing import Sequence
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.compatibility.config import AICompatibilityConfig, default_compatibility_config
from app.core.compatibility.engine import AICompatibilityEngine, default_compatibility_engine
from app.core.compatibility.models import CompatibilityReport, PlayerComparisonInput
from app.models.gamer_dna import GamerDNA
from app.models.gamer_profile import GamerProfile
from app.models.player_stat import PlayerStat
from app.models.user import User
from app.repositories.dna_repository import DNARepository
from app.repositories.player_stat_repository import PlayerStatRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.compatibility import CompatibilityCompareRequest, CompatibilityReportResponse
from app.services.base import BaseService


class AICompatibilityService(BaseService[User]):
    """
    Service layer orchestrating 10-dimensional player compatibility comparisons.
    """

    def __init__(
        self,
        db: AsyncSession,
        engine: AICompatibilityEngine | None = None,
        user_repo: UserRepository | None = None,
        profile_repo: ProfileRepository | None = None,
        dna_repo: DNARepository | None = None,
        player_stat_repo: PlayerStatRepository | None = None,
        config: AICompatibilityConfig | None = None,
    ) -> None:
        super().__init__(db)
        self.config = config or default_compatibility_config
        self.engine = engine or default_compatibility_engine
        self.user_repo = user_repo or UserRepository(db)
        self.profile_repo = profile_repo or ProfileRepository(db)
        self.dna_repo = dna_repo or DNARepository(db)
        self.player_stat_repo = player_stat_repo or PlayerStatRepository(db)

    def compare_payload(
        self,
        request: CompatibilityCompareRequest,
    ) -> CompatibilityReport:
        """Compares two player profiles directly from an API request payload."""
        p_a = request.player_a
        p_b = request.player_b

        input_a = PlayerComparisonInput(
            username=p_a.username,
            leadership=p_a.leadership,
            communication=p_a.communication,
            aggression=p_a.aggression,
            strategy=p_a.strategy,
            region=p_a.region,
            languages=p_a.languages,
            schedule_slots=p_a.schedule_slots,
            rank_rating=p_a.rank_rating,
            rank_tier=p_a.rank_tier,
            win_rate=p_a.win_rate,
            preferred_roles=p_a.preferred_roles,
        )

        input_b = PlayerComparisonInput(
            username=p_b.username,
            leadership=p_b.leadership,
            communication=p_b.communication,
            aggression=p_b.aggression,
            strategy=p_b.strategy,
            region=p_b.region,
            languages=p_b.languages,
            schedule_slots=p_b.schedule_slots,
            rank_rating=p_b.rank_rating,
            rank_tier=p_b.rank_tier,
            win_rate=p_b.win_rate,
            preferred_roles=p_b.preferred_roles,
        )

        return self.engine.compare(input_a, input_b)

    async def compare_users(
        self,
        user_a_id: uuid.UUID,
        user_b_id: uuid.UUID,
    ) -> CompatibilityReport:
        """
        Gathers database entities (User, GamerProfile, GamerDNA, PlayerStats) for two users
        and computes their pairwise compatibility report.
        """
        if user_a_id == user_b_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot compare a user with themselves.",
            )

        # 1. Fetch User A & User B
        user_a = await self.user_repo.get_by_id(user_a_id)
        user_b = await self.user_repo.get_by_id(user_b_id)

        if not user_a or not user_b:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both users not found.",
            )

        input_a = await self._build_player_input(user_a)
        input_b = await self._build_player_input(user_b)

        return self.engine.compare(input_a, input_b)

    async def _build_player_input(self, user: User) -> PlayerComparisonInput:
        """Hydrates a PlayerComparisonInput from the user's database records."""
        # Fetch DNA
        dna = await self.dna_repo.get_by_user_id(user.id)
        leadership = float(dna.leadership) if (dna and dna.leadership is not None) else 50.0
        communication = float(dna.communication) if (dna and dna.communication is not None) else 50.0
        aggression = float(dna.aggression) if (dna and dna.aggression is not None) else 50.0
        strategy = float(dna.strategy) if (dna and dna.strategy is not None) else 50.0

        # Fetch Profile
        profile = await self.profile_repo.get_by_user_id(user.id)
        region = profile.region if profile and profile.region else "NA-East"
        languages = [profile.language] if profile and profile.language else ["en"]
        preferred_roles = list(profile.preferred_roles or []) if profile else []
        schedule_slots: list[str] = []
        if profile and profile.availability and isinstance(profile.availability, dict):
            schedule_slots = profile.availability.get("active_slots", [])

        # Fetch PlayerStats
        stats = await self.player_stat_repo.get_by_user_id(user.id)
        if stats:
            total_matches = sum(s.matches_played for s in stats)
            if total_matches > 0:
                win_rate = sum(s.win_rate * s.matches_played for s in stats) / total_matches
            else:
                win_rate = sum(s.win_rate for s in stats) / len(stats)
            rank_rating = max((s.rank_rating for s in stats), default=1000)
            rank_tier = stats[0].current_rank if stats[0].current_rank else None
        else:
            win_rate = 50.0
            rank_rating = 1000
            rank_tier = None

        return PlayerComparisonInput(
            user_id=user.id,
            username=user.username,
            leadership=leadership,
            communication=communication,
            aggression=aggression,
            strategy=strategy,
            region=region,
            languages=languages,
            schedule_slots=schedule_slots,
            rank_rating=rank_rating,
            rank_tier=rank_tier,
            win_rate=round(win_rate, 2),
            preferred_roles=preferred_roles,
        )
