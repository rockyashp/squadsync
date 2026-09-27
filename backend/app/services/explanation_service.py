"""
AI Explanation Service orchestrating template-based compatibility and synergy explanations.
Integrates AIExplanationEngine, AICompatibilityEngine, and database repositories.
"""

from typing import Sequence
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.compatibility.engine import AICompatibilityEngine, default_compatibility_engine
from app.core.compatibility.models import CompatibilityReport, PlayerComparisonInput
from app.core.explanation.config import ExplanationConfig, default_explanation_config
from app.core.explanation.engine import (
    AIExplanationEngine,
    ExplanationResult,
    PlayerExplanationContext,
    default_explanation_engine,
)
from app.models.gamer_dna import GamerDNA
from app.models.gamer_profile import GamerProfile
from app.models.player_stat import PlayerStat
from app.models.user import User
from app.repositories.dna_repository import DNARepository
from app.repositories.player_stat_repository import PlayerStatRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.explanation import (
    ExplanationCompareRequest,
    ExplanationResponse,
    PlayerExplanationInputSchema,
)
from app.services.base import BaseService


class AIExplanationService(BaseService[User]):
    """
    Service layer providing natural language explanations for player compatibility.
    """

    def __init__(
        self,
        db: AsyncSession,
        engine: AIExplanationEngine | None = None,
        compatibility_engine: AICompatibilityEngine | None = None,
        user_repo: UserRepository | None = None,
        profile_repo: ProfileRepository | None = None,
        dna_repo: DNARepository | None = None,
        player_stat_repo: PlayerStatRepository | None = None,
        config: ExplanationConfig | None = None,
    ) -> None:
        super().__init__(db)
        self.config = config or default_explanation_config
        self.engine = engine or default_explanation_engine
        self.compatibility_engine = compatibility_engine or default_compatibility_engine
        self.user_repo = user_repo or UserRepository(db)
        self.profile_repo = profile_repo or ProfileRepository(db)
        self.dna_repo = dna_repo or DNARepository(db)
        self.player_stat_repo = player_stat_repo or PlayerStatRepository(db)

    def explain_payload(self, request: ExplanationCompareRequest) -> ExplanationResponse:
        """
        Generates human-readable explanation from explicit request payload.
        """
        ctx_a = self._convert_schema_to_context(request.player_a)
        ctx_b = self._convert_schema_to_context(request.player_b)

        # Run compatibility engine comparison
        comp_input_a = self._convert_context_to_comp_input(ctx_a)
        comp_input_b = self._convert_context_to_comp_input(ctx_b)
        report = self.compatibility_engine.compare(comp_input_a, comp_input_b)

        # Run explanation engine
        result = self.engine.generate_explanation(
            player_a=ctx_a,
            player_b=ctx_b,
            compatibility_report=report,
        )

        return self._format_response(result, ctx_a.username, ctx_b.username)

    async def explain_between_users(
        self,
        user_a_id: uuid.UUID,
        user_b_id: uuid.UUID,
    ) -> ExplanationResponse:
        """
        Gathers database entities for both users, evaluates pairwise compatibility,
        and generates comprehensive natural language explanation.
        """
        if user_a_id == user_b_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot generate compatibility explanation for a user with themselves.",
            )

        # 1. Fetch Users
        user_a = await self.user_repo.get_by_id(user_a_id)
        user_b = await self.user_repo.get_by_id(user_b_id)

        if not user_a or not user_b:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both users not found.",
            )

        ctx_a = await self._build_player_context(user_a)
        ctx_b = await self._build_player_context(user_b)

        comp_input_a = self._convert_context_to_comp_input(ctx_a)
        comp_input_b = self._convert_context_to_comp_input(ctx_b)
        report = self.compatibility_engine.compare(comp_input_a, comp_input_b)

        result = self.engine.generate_explanation(
            player_a=ctx_a,
            player_b=ctx_b,
            compatibility_report=report,
        )

        return self._format_response(result, ctx_a.username, ctx_b.username)

    # --------------------------------------------------------------------------
    # Hydration & Conversion Helpers
    # --------------------------------------------------------------------------

    async def _build_player_context(self, user: User) -> PlayerExplanationContext:
        """Hydrates PlayerExplanationContext from database."""
        # 1. DNA
        dna = await self.dna_repo.get_by_user_id(user.id)
        leadership = float(dna.leadership) if (dna and dna.leadership is not None) else 50.0
        communication = float(dna.communication) if (dna and dna.communication is not None) else 50.0
        aggression = float(dna.aggression) if (dna and dna.aggression is not None) else 50.0
        strategy = float(dna.strategy) if (dna and dna.strategy is not None) else 50.0
        teamwork = float(dna.teamwork) if (dna and dna.teamwork is not None) else 50.0
        confidence = float(getattr(dna, "confidence", 50.0) or 50.0) if dna else 50.0
        primary_role = dna.primary_role if (dna and dna.primary_role) else "Support"
        secondary_role = dna.secondary_role if (dna and dna.secondary_role) else None

        # 2. Profile
        profile = await self.profile_repo.get_by_user_id(user.id)
        region = profile.region if (profile and profile.region) else "NA-East"
        languages = [profile.language] if (profile and profile.language) else ["en"]
        preferred_roles = list(profile.preferred_roles or []) if profile else [primary_role]
        schedule_slots: list[str] = []
        if profile and profile.availability and isinstance(profile.availability, dict):
            schedule_slots = profile.availability.get("active_slots", [])

        # 3. Stats
        stats = await self.player_stat_repo.get_by_user_id(user.id)
        if stats:
            total_matches = sum(s.matches_played for s in stats)
            win_rate = (
                sum(s.win_rate * s.matches_played for s in stats) / total_matches
                if total_matches > 0
                else sum(s.win_rate for s in stats) / len(stats)
            )
            rank_rating = max((s.rank_rating for s in stats), default=1000)
            rank_tier = stats[0].current_rank or "Gold 1"
            matches_played = total_matches
            kd_ratio = float(stats[0].kd_ratio) if stats[0].kd_ratio is not None else 1.0
        else:
            win_rate = 50.0
            rank_rating = 1000
            rank_tier = "Gold 1"
            matches_played = 20
            kd_ratio = 1.0

        username = user.username or f"player_{str(user.id)[:8]}"

        return PlayerExplanationContext(
            username=username,
            leadership=leadership,
            communication=communication,
            aggression=aggression,
            strategy=strategy,
            teamwork=teamwork,
            confidence=confidence,
            primary_role=primary_role,
            secondary_role=secondary_role,
            preferred_roles=preferred_roles,
            rank=rank_tier,
            rank_rating=rank_rating,
            win_rate=round(win_rate, 2),
            matches_played=matches_played,
            kd_ratio=kd_ratio,
            region=region,
            languages=languages,
            schedule_slots=schedule_slots,
        )

    def _convert_schema_to_context(self, s: PlayerExplanationInputSchema) -> PlayerExplanationContext:
        """Converts Pydantic input schema to PlayerExplanationContext dataclass."""
        return PlayerExplanationContext(
            username=s.username,
            leadership=s.leadership,
            communication=s.communication,
            aggression=s.aggression,
            strategy=s.strategy,
            teamwork=s.teamwork,
            primary_role=s.primary_role,
            secondary_role=s.secondary_role,
            preferred_roles=s.preferred_roles or [s.primary_role],
            rank=s.rank,
            rank_rating=s.rank_rating,
            win_rate=s.win_rate,
            matches_played=s.matches_played,
            kd_ratio=s.kd_ratio,
            region=s.region,
            languages=s.languages,
            schedule_slots=s.schedule_slots,
        )

    def _convert_context_to_comp_input(self, c: PlayerExplanationContext) -> PlayerComparisonInput:
        """Converts PlayerExplanationContext to PlayerComparisonInput for compatibility engine."""
        return PlayerComparisonInput(
            username=c.username,
            leadership=c.leadership,
            communication=c.communication,
            aggression=c.aggression,
            strategy=c.strategy,
            region=c.region,
            languages=c.languages,
            schedule_slots=c.schedule_slots,
            rank_rating=c.rank_rating,
            rank_tier=c.rank,
            win_rate=c.win_rate,
            preferred_roles=c.preferred_roles or [c.primary_role],
        )

    def _format_response(
        self,
        res: ExplanationResult,
        player_a_name: str,
        player_b_name: str,
    ) -> ExplanationResponse:
        """Formats internal ExplanationResult into client API ExplanationResponse."""
        return ExplanationResponse(
            headline=res.headline,
            player_a_name=player_a_name,
            player_b_name=player_b_name,
            compatibility_score=res.compatibility_score,
            tier=res.tier,
            why_they_match=res.match_reasons,
            why_they_dont_match=res.mismatch_reasons,
            strengths=res.strengths_narrative,
            weaknesses=res.weaknesses_narrative,
            improvement_suggestions=res.improvement_suggestions,
            confidence_score=res.confidence_score,
        )
