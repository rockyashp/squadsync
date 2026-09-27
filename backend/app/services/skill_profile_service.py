"""
SkillProfileService orchestrating multi-signal competitive skill evaluation.
Fuses Survey psychometrics, Gamer DNA, and official game telemetry from all linked accounts.
"""

from datetime import datetime, timezone
from typing import Any, Sequence
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.role_classifier.features import GamerDNAVector, OfficialGameStats
from app.core.skill_profile.config import SkillProfileConfig, default_skill_config
from app.core.skill_profile.engine import SkillProfileEngine, SkillProfileResult, default_skill_engine
from app.models.gamer_dna import GamerDNA
from app.models.player_stat import PlayerStat
from app.repositories.dna_repository import DNARepository
from app.repositories.player_stat_repository import PlayerStatRepository
from app.repositories.survey_repository import SurveyRepository
from app.schemas.skill_profile import (
    SkillDimensionDetail,
    SkillProfileEvaluateRequest,
    SkillProfileResponse,
)
from app.services.base import BaseService


class SkillProfileService(BaseService[GamerDNA]):
    """
    Service layer orchestrating the generation and persistence of
    6-dimensional player skill profiles.
    """

    def __init__(
        self,
        db: AsyncSession,
        engine: SkillProfileEngine | None = None,
        dna_repo: DNARepository | None = None,
        player_stat_repo: PlayerStatRepository | None = None,
        survey_repo: SurveyRepository | None = None,
        config: SkillProfileConfig | None = None,
    ) -> None:
        super().__init__(db)
        self.config = config or default_skill_config
        self.engine = engine or default_skill_engine
        self.dna_repo = dna_repo or DNARepository(db)
        self.player_stat_repo = player_stat_repo or PlayerStatRepository(db)
        self.survey_repo = survey_repo or SurveyRepository(db)

    def evaluate_payload(
        self,
        request: SkillProfileEvaluateRequest,
    ) -> SkillProfileResult:
        """Evaluates skill profile directly against an input payload."""
        dna = GamerDNAVector(
            leadership=request.gamer_dna.leadership,
            communication=request.gamer_dna.communication,
            strategy=request.gamer_dna.strategy,
            teamwork=request.gamer_dna.teamwork,
            aggression=request.gamer_dna.aggression,
            confidence=request.gamer_dna.confidence,
        )
        stats = OfficialGameStats(
            win_rate=request.official_stats.win_rate,
            kd_ratio=request.official_stats.kd_ratio,
            kda=request.official_stats.kda,
            matches_played=request.official_stats.matches_played,
            headshot_pct=request.official_stats.headshot_pct,
            score_per_round=request.official_stats.score_per_round,
            rank=request.official_stats.rank,
            rank_rating=request.official_stats.rank_rating,
            favorite_heroes_or_agents=list(request.official_stats.favorite_heroes_or_agents),
        )
        return self.engine.generate(dna, stats)

    async def generate_for_user(
        self,
        user_id: uuid.UUID,
        persist: bool = True,
    ) -> SkillProfileResult:
        """
        Hydrates stored user DNA, survey answers, and cross-game player stats from the database,
        executes the 6 skill evaluators, and optionally persists results into GamerDNA.
        """
        # 1. Fetch GamerDNA record
        dna_record = await self.dna_repo.get_by_user_id(user_id)
        if dna_record:
            dna = GamerDNAVector(
                leadership=float(dna_record.leadership),
                communication=float(dna_record.communication),
                strategy=float(dna_record.strategy),
                teamwork=float(dna_record.teamwork),
                aggression=float(dna_record.aggression),
                confidence=float(getattr(dna_record, "confidence", 50) or 50),
            )
        else:
            # Fallback to survey answers if DNA record not yet generated
            survey_answers = await self.survey_repo.get_answers_by_user_id(user_id)
            dna = self._derive_dna_from_answers(survey_answers)

        # 2. Fetch PlayerStats across all game accounts
        stat_records = await self.player_stat_repo.get_by_user_id(user_id)
        stats = self._aggregate_player_stats(stat_records)

        # 3. Execute Skill Profile Engine
        result = self.engine.generate(dna, stats)

        # 4. Optionally persist into gamer_dna raw_evaluation
        if persist:
            await self._persist_skill_profile(user_id, result, dna_record)

        return result

    def _derive_dna_from_answers(self, answers: Sequence[Any]) -> GamerDNAVector:
        """Aggregates survey answer scores per category into a fallback GamerDNAVector."""
        if not answers:
            return GamerDNAVector()

        from collections import defaultdict
        category_scores: dict[str, list[int]] = defaultdict(list)
        for a in answers:
            if hasattr(a, "category") and a.category and hasattr(a, "score") and a.score is not None:
                category_scores[a.category].append(a.score)

        def avg_cat(cat: str) -> float:
            vals = category_scores.get(cat, [])
            return float(sum(vals) / len(vals)) if vals else 50.0

        return GamerDNAVector(
            leadership=avg_cat("Leadership"),
            communication=avg_cat("Communication"),
            strategy=avg_cat("Strategy"),
            teamwork=avg_cat("Teamwork"),
            aggression=avg_cat("Aggression"),
            confidence=avg_cat("Confidence"),
        )

    def _aggregate_player_stats(self, records: Sequence[PlayerStat]) -> OfficialGameStats:
        """Aggregates competitive telemetry across multiple connected accounts."""
        if not records:
            return OfficialGameStats(
                win_rate=50.0,
                kd_ratio=1.0,
                kda=2.0,
                matches_played=0,
                headshot_pct=None,
            )

        total_matches = sum(r.matches_played for r in records)
        if total_matches == 0:
            avg_wr = sum(r.win_rate for r in records) / len(records)
            avg_kd = sum(r.kd_ratio for r in records) / len(records)
            avg_kda = sum(r.kda for r in records) / len(records)
            return OfficialGameStats(
                win_rate=round(avg_wr, 2),
                kd_ratio=round(avg_kd, 2),
                kda=round(avg_kda, 2),
                matches_played=0,
            )

        weighted_wr = sum(r.win_rate * r.matches_played for r in records) / total_matches
        weighted_kd = sum(r.kd_ratio * r.matches_played for r in records) / total_matches
        weighted_kda = sum(r.kda * r.matches_played for r in records) / total_matches

        hs_records = [r for r in records if r.headshot_pct is not None]
        avg_hs = (
            sum(r.headshot_pct * r.matches_played for r in hs_records) / sum(r.matches_played for r in hs_records)
            if hs_records and sum(r.matches_played for r in hs_records) > 0
            else None
        )

        return OfficialGameStats(
            win_rate=round(weighted_wr, 2),
            kd_ratio=round(weighted_kd, 2),
            kda=round(weighted_kda, 2),
            matches_played=total_matches,
            headshot_pct=round(avg_hs, 2) if avg_hs is not None else None,
        )

    async def _persist_skill_profile(
        self,
        user_id: uuid.UUID,
        result: SkillProfileResult,
        existing_dna: GamerDNA | None,
    ) -> None:
        """Saves skill profile into GamerDNA.raw_evaluation JSONB payload."""
        now = datetime.now(timezone.utc)
        payload = {
            "overall_score": result.overall_score,
            "overall_tier": result.overall_tier,
            "radar_chart": result.radar_chart,
            "top_strengths": result.top_strengths,
            "growth_areas": result.growth_areas,
            "evaluated_at": now.isoformat(),
        }

        if existing_dna:
            raw_eval = dict(existing_dna.raw_evaluation or {})
            raw_eval["skill_profile"] = payload
            existing_dna.raw_evaluation = raw_eval
            existing_dna.updated_at = now
            await self.dna_repo.update(existing_dna)
        else:
            new_dna = GamerDNA(
                id=uuid.uuid4(),
                user_id=user_id,
                leadership=50,
                communication=50,
                strategy=50,
                teamwork=50,
                aggression=50,
                confidence=50,
                primary_role="Flex",
                secondary_role="Support",
                personality="The Adaptive Player",
                raw_evaluation={"skill_profile": payload},
                created_at=now,
                updated_at=now,
            )
            await self.dna_repo.create(new_dna)
