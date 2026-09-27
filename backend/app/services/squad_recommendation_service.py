"""
Squad Recommendation Service.
Orchestrates candidate retrieval from CandidateRepository and runs the SquadRecommendationEngine.
"""

from typing import Sequence
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.squad_recommendation.config import SquadRecommendationConfig, default_squad_config
from app.core.squad_recommendation.engine import (
    SquadRecommendationEngine,
    SquadRecommendationResult,
)
from app.models.user import User
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.user_repository import UserRepository
from app.schemas.matchmaking import MatchmakingCandidate
from app.services.base import BaseService


class SquadRecommendationService(BaseService[User]):
    """
    Service layer coordinating candidate querying and 5-player squad optimization.
    """

    def __init__(
        self,
        db: AsyncSession,
        candidate_repo: CandidateRepository | None = None,
        user_repo: UserRepository | None = None,
        engine: SquadRecommendationEngine | None = None,
        config: SquadRecommendationConfig | None = None,
    ) -> None:
        super().__init__(db)
        self.config = config or default_squad_config
        self.candidate_repo = candidate_repo or CandidateRepository(db)
        self.user_repo = user_repo or UserRepository(db)
        self.engine = engine or SquadRecommendationEngine(config=self.config)

    async def recommend_for_user(
        self,
        user_id: uuid.UUID,
        game_name: str = "Valorant",
        target_region: str | None = None,
        pool_limit: int = 40,
    ) -> SquadRecommendationResult:
        """
        Retrieves requesting player and active candidate pool, and generates the Top 10 teammates
        and Best 5-player squad.
        """
        # 1. Fetch Current User
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            # Fallback mock entity for unseeded/testing IDs
            user = User(
                id=user_id,
                username=f"player_{str(user_id)[:8]}",
                email=f"player_{str(user_id)[:8]}@squadsync.gg",
                password_hash="mock_hash",
                is_active=True,
            )

        current_user_candidate = await self.candidate_repo.build_candidate_for_user(
            user=user,
            target_game=game_name,
        )

        # 2. Query Candidate Pool
        candidates = await self.candidate_repo.get_candidate_pool(
            exclude_user_id=user_id,
            target_game=game_name,
            target_region=target_region,
            limit=pool_limit,
        )

        # 3. Fallback: if candidate pool has fewer than 4 candidates, generate tactical archetypes
        if len(candidates) < 4:
            candidates = self._generate_archetype_pool(current_user_candidate, game_name)

        # 4. Execute Squad Recommendation Engine
        return self.engine.generate_recommendation(
            current_user=current_user_candidate,
            candidates=candidates,
            game_name=game_name,
        )

    def evaluate_explicit_candidates(
        self,
        current_user: MatchmakingCandidate,
        candidates: Sequence[MatchmakingCandidate],
        game_name: str = "Valorant",
    ) -> SquadRecommendationResult:
        """Evaluates explicitly passed candidate objects."""
        pool = list(candidates)
        if len(pool) < 4:
            pool.extend(self._generate_archetype_pool(current_user, game_name))

        return self.engine.generate_recommendation(
            current_user=current_user,
            candidates=pool,
            game_name=game_name,
        )

    def _generate_archetype_pool(
        self,
        current_user: MatchmakingCandidate,
        game_name: str,
    ) -> list[MatchmakingCandidate]:
        """Generates representative candidate archetypes across essential roles to guarantee full comp evaluation."""
        archetypes = [
            ("Duelist", "The Aggressive Entry", 88, 75, 92, 65, 80),
            ("Controller", "The Spatial Smoker", 55, 82, 45, 88, 80),
            ("Sentinel", "The Lockdown Anchor", 50, 80, 40, 90, 85),
            ("Support", "The Tactical Lifeline", 60, 92, 35, 75, 95),
            ("Strategist", "The Macro Shotcaller", 85, 85, 55, 95, 75),
            ("Leader", "The Inspirational IGL", 90, 90, 60, 85, 70),
        ]

        pool: list[MatchmakingCandidate] = []
        for i, (role, moniker, lead, comm, aggr, strat, team) in enumerate(archetypes):
            cid = uuid.uuid4()
            pool.append(
                MatchmakingCandidate(
                    user_id=cid,
                    username=f"tactical_{role.lower()}_{i+1}",
                    display_name=f"Tactical {role}",
                    primary_role=role,
                    secondary_role="Support" if role != "Support" else "Sentinel",
                    personality=moniker,
                    rank=current_user.rank,
                    mmr=current_user.mmr + (i * 25 - 50),
                    win_rate=54.5,
                    matches_played=60,
                    kd_ratio=1.2,
                    leadership=lead,
                    communication=comm,
                    aggression=aggr,
                    strategy=strat,
                    teamwork=team,
                    confidence=75,
                    region=current_user.region,
                    languages=current_user.languages,
                    schedule_tags=current_user.schedule_tags,
                    preferred_games=[game_name],
                    preferred_roles=[role],
                )
            )
        return pool
