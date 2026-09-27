"""
Unified AI Service coordinating all platform AI sub-engines.
Orchestrates Gamer DNA, Role Classification, Skill Profiling,
Pairwise Compatibility, Squad Recommendation, and Natural Language Explanations.
"""

from typing import Sequence
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.ai import (
    CompatibilityMeResponse,
    ExplanationMeResponse,
    GamerDNAMeResponse,
    RecommendationsMeResponse,
    RoleClassificationMeResponse,
    SkillProfileMeResponse,
    SquadMeResponse,
)
from app.schemas.compatibility import CompatibilityReportResponse
from app.schemas.dna import GamerDNACardResponse
from app.schemas.explanation import ExplanationResponse
from app.schemas.role_classifier import RoleClassificationResponse
from app.schemas.skill_profile import SkillProfileResponse
from app.schemas.squad_recommendation import (
    BestSquadCompositionSchema,
    BestSquadMemberSchema,
    TeammateCandidateSchema,
)
from app.services.base import BaseService
from app.services.compatibility_service import AICompatibilityService
from app.services.dna_service import DNAService
from app.services.explanation_service import AIExplanationService
from app.services.role_classifier_service import RoleClassifierService
from app.services.skill_profile_service import SkillProfileService
from app.services.squad_recommendation_service import SquadRecommendationService


class AIService(BaseService[User]):
    """
    Central orchestration service for the unified FastAPI AI Module.
    """

    def __init__(
        self,
        db: AsyncSession,
        dna_service: DNAService | None = None,
        role_classifier_service: RoleClassifierService | None = None,
        skill_profile_service: SkillProfileService | None = None,
        compatibility_service: AICompatibilityService | None = None,
        squad_service: SquadRecommendationService | None = None,
        explanation_service: AIExplanationService | None = None,
    ) -> None:
        super().__init__(db)
        self.dna_service = dna_service or DNAService(db)
        self.role_classifier_service = role_classifier_service or RoleClassifierService(db)
        self.skill_profile_service = skill_profile_service or SkillProfileService(db)
        self.compatibility_service = compatibility_service or AICompatibilityService(db)
        self.squad_service = squad_service or SquadRecommendationService(db)
        self.explanation_service = explanation_service or AIExplanationService(db)

    async def get_my_dna(self, user: User) -> GamerDNAMeResponse:
        """Retrieves authenticated user's Gamer DNA analysis card."""
        card = await self.dna_service.get_gamer_dna_card(user=user)
        return GamerDNAMeResponse(dna=card)

    async def get_my_role(self, user_id: uuid.UUID) -> RoleClassificationMeResponse:
        """Generates AI Role Classification for authenticated user."""
        res = await self.role_classifier_service.evaluate_user(user_id=user_id, persist=True)
        return RoleClassificationMeResponse(
            classification=RoleClassificationResponse(
                primary_role=res.primary_role,
                secondary_role=res.secondary_role,
                confidence_score=res.confidence_score,
                reasoning=res.reasoning,
                personality=res.personality,
                role_affinities=res.role_affinities,
                signal_contributions=res.signal_contributions,
                feature_importance=res.feature_importance,
            )
        )

    async def get_my_skill_profile(self, user_id: uuid.UUID) -> SkillProfileMeResponse:
        """Generates Six-Axis AI Skill Profile for authenticated user."""
        from app.routers.api_v1.endpoints.skill_profile import _to_response_dto
        result = await self.skill_profile_service.generate_for_user(user_id=user_id, persist=False)
        return SkillProfileMeResponse(skill_profile=_to_response_dto(result))

    async def get_compatibility_with_user(
        self,
        current_user_id: uuid.UUID,
        target_user_id: uuid.UUID,
    ) -> CompatibilityMeResponse:
        """Calculates 10-dimensional pairwise compatibility between requester and target user."""
        report = await self.compatibility_service.compare_users(
            user_a_id=current_user_id,
            user_b_id=target_user_id,
        )
        compat_resp = CompatibilityReportResponse(
            player_a_name=report.player_a_name,
            player_b_name=report.player_b_name,
            compatibility_score=report.compatibility_score,
            tier=report.tier,
            dimension_scores=report.dimension_scores,
            strengths=report.strengths,
            weaknesses=report.weaknesses,
            recommendations=report.recommendations,
            risk_factors=report.risk_factors,
        )
        return CompatibilityMeResponse(compatibility=compat_resp)

    async def get_teammate_recommendations(
        self,
        user_id: uuid.UUID,
        game_name: str = "Valorant",
        limit: int = 40,
    ) -> RecommendationsMeResponse:
        """Generates Top 10 recommended teammates for the authenticated user."""
        result = await self.squad_service.recommend_for_user(
            user_id=user_id,
            game_name=game_name,
            pool_limit=limit,
        )
        top_candidates = [
            TeammateCandidateSchema(
                user_id=str(t.user_id),
                username=t.username,
                compatibility_score=t.compatibility_score,
                primary_role=t.primary_role,
                secondary_role=t.secondary_role,
                rank=t.rank or "Unranked",
                mmr=t.mmr,
                win_rate=t.win_rate,
                personality=t.personality,
                synergy_highlights=t.synergy_highlights,
            )
            for t in result.top_10_teammates
        ]
        return RecommendationsMeResponse(
            current_user_id=str(user_id),
            target_game=game_name,
            top_teammates=top_candidates,
        )

    async def get_optimal_squad(
        self,
        user_id: uuid.UUID,
        game_name: str = "Valorant",
        limit: int = 40,
    ) -> SquadMeResponse:
        """Computes optimal 5-player squad composition containing the authenticated user."""
        result = await self.squad_service.recommend_for_user(
            user_id=user_id,
            game_name=game_name,
            pool_limit=limit,
        )
        best_squad = result.best_5_player_squad
        members_schema = [
            BestSquadMemberSchema(
                user_id=str(m.user_id),
                username=m.username,
                primary_role=m.primary_role,
                secondary_role=m.secondary_role,
                rank=m.rank or "Unranked",
                mmr=m.mmr,
                win_rate=m.win_rate,
            )
            for m in best_squad.members
        ]
        composition_schema = BestSquadCompositionSchema(
            overall_score=best_squad.overall_score,
            compatibility_score=best_squad.compatibility_score,
            role_balance_score=best_squad.role_balance_score,
            skill_balance_score=best_squad.skill_balance_score,
            communication_score=best_squad.communication_score,
            leadership_score=best_squad.leadership_score,
            designated_igl=best_squad.designated_igl,
            mean_mmr=best_squad.mean_mmr,
            skill_variance=best_squad.skill_variance,
            role_distribution=best_squad.role_distribution,
            missing_roles=best_squad.missing_roles,
            members=members_schema,
            synergy_reasons=best_squad.synergy_reasons,
        )
        return SquadMeResponse(
            current_user_id=str(user_id),
            target_game=game_name,
            squad=composition_schema,
            missing_roles=result.missing_roles,
            confidence_score=result.confidence_score,
        )

    async def get_explanation_with_user(
        self,
        current_user_id: uuid.UUID,
        target_user_id: uuid.UUID,
    ) -> ExplanationMeResponse:
        """Generates natural language explanation and coaching tips between requester and target user."""
        res = await self.explanation_service.explain_between_users(
            user_a_id=current_user_id,
            user_b_id=target_user_id,
        )
        return ExplanationMeResponse(explanation=res)
