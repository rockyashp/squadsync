"""
RoleClassifierService orchestrating multi-signal gamer role classification.
Coordinates feature extraction, rule evaluation (or ML inference), database hydration,
and GamerDNA persistence.
"""

from datetime import datetime, timezone
from typing import Any, Sequence
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.role_classifier.base import (
    BaseRoleClassifier,
    RoleClassificationResult,
)
from app.core.role_classifier.config import (
    RoleClassificationConfig,
    default_classification_config,
)
from app.core.role_classifier.engine import RuleBasedRoleClassifier
from app.core.role_classifier.features import (
    GamerDNAVector,
    GamerRoleFeatures,
    OfficialGameStats,
)
from app.models.gamer_dna import GamerDNA
from app.models.player_stat import PlayerStat
from app.repositories.dna_repository import DNARepository
from app.repositories.player_stat_repository import PlayerStatRepository
from app.repositories.profile_repository import ProfileRepository
from app.schemas.role_classifier import (
    RoleClassificationResponse,
    RoleClassifierConfigResponse,
    RoleClassifierEvaluateRequest,
)
from app.services.base import BaseService


class RoleClassifierService(BaseService[GamerDNA]):
    """
    Service layer orchestrating the Gamer Role Classification Engine.
    Decoupled via BaseRoleClassifier strategy pattern to allow seamless
    switching between Rule-Based logic and Machine Learning models.
    """

    def __init__(
        self,
        db: AsyncSession,
        classifier: BaseRoleClassifier | None = None,
        dna_repo: DNARepository | None = None,
        player_stat_repo: PlayerStatRepository | None = None,
        profile_repo: ProfileRepository | None = None,
        config: RoleClassificationConfig | None = None,
    ) -> None:
        super().__init__(db)
        self.config = config or default_classification_config
        self.classifier: BaseRoleClassifier = classifier or RuleBasedRoleClassifier(config=self.config)
        self.dna_repo = dna_repo or DNARepository(db)
        self.player_stat_repo = player_stat_repo or PlayerStatRepository(db)
        self.profile_repo = profile_repo or ProfileRepository(db)

    def evaluate_payload(
        self,
        request: RoleClassifierEvaluateRequest,
    ) -> RoleClassificationResult:
        """
        Executes classification directly against an input payload containing the 4 inputs:
        1. Gamer DNA feature vector
        2. Official game statistics
        3. Preferred roles
        4. Preferred games
        """
        # 1. Build GamerDNAVector
        dna = GamerDNAVector(
            leadership=request.gamer_dna.leadership,
            communication=request.gamer_dna.communication,
            strategy=request.gamer_dna.strategy,
            teamwork=request.gamer_dna.teamwork,
            aggression=request.gamer_dna.aggression,
            confidence=request.gamer_dna.confidence,
        )

        # 2. Build OfficialGameStats
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

        # 3. Assemble consolidated GamerRoleFeatures
        features = GamerRoleFeatures(
            dna=dna,
            stats=stats,
            preferred_roles=request.preferred_roles,
            preferred_games=request.preferred_games,
        )

        # 4. Execute classification (rule-based or ML adapter)
        return self.classifier.classify(features)

    async def evaluate_user(
        self,
        user_id: uuid.UUID,
        persist: bool = True,
    ) -> RoleClassificationResult:
        """
        Gathers stored user profile, Gamer DNA psychometrics, and official game statistics
        from the database, executes role classification, and optionally updates the user's
        GamerDNA record.
        """
        # 1. Fetch GamerDNA
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
            # Neutral default baseline if user has not yet taken the survey
            dna = GamerDNAVector(
                leadership=50.0,
                communication=50.0,
                strategy=50.0,
                teamwork=50.0,
                aggression=50.0,
                confidence=50.0,
            )

        # 2. Fetch PlayerStats across all connected game accounts
        stat_records = await self.player_stat_repo.get_by_user_id(user_id)
        stats = self._aggregate_player_stats(stat_records)

        # 3. Fetch GamerProfile
        profile_record = await self.profile_repo.get_by_user_id(user_id)
        preferred_roles: list[str] = []
        preferred_games: list[str] = []
        if profile_record:
            preferred_roles = list(profile_record.preferred_roles or [])
            preferred_games = list(profile_record.preferred_games or [])

        # 4. Construct feature vector and classify
        features = GamerRoleFeatures(
            dna=dna,
            stats=stats,
            preferred_roles=preferred_roles,
            preferred_games=preferred_games,
        )
        result = self.classifier.classify(features)

        # 5. Optionally persist to database
        if persist:
            await self._persist_classification(user_id, result, dna_record)

        return result

    def _aggregate_player_stats(
        self,
        records: Sequence[PlayerStat],
    ) -> OfficialGameStats:
        """
        Aggregates multiple game accounts and season stats into a single
        weighted official telemetry profile.
        """
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

        # Weighted calculations based on match volume
        weighted_wr = sum(r.win_rate * r.matches_played for r in records) / total_matches
        weighted_kd = sum(r.kd_ratio * r.matches_played for r in records) / total_matches
        weighted_kda = sum(r.kda * r.matches_played for r in records) / total_matches

        # Headshot % average if available
        hs_records = [r for r in records if r.headshot_pct is not None]
        avg_hs = (
            sum(r.headshot_pct * r.matches_played for r in hs_records) / sum(r.matches_played for r in hs_records)
            if hs_records and sum(r.matches_played for r in hs_records) > 0
            else None
        )

        # Collect favorite heroes/agents from raw telemetry if present
        heroes: list[str] = []
        for r in records:
            if r.raw_stats and isinstance(r.raw_stats, dict):
                favs = r.raw_stats.get("favorite_heroes") or r.raw_stats.get("preferred_agent")
                if isinstance(favs, list):
                    heroes.extend(str(h) for h in favs)
                elif isinstance(favs, str):
                    heroes.append(favs)

        return OfficialGameStats(
            win_rate=round(weighted_wr, 2),
            kd_ratio=round(weighted_kd, 2),
            kda=round(weighted_kda, 2),
            matches_played=total_matches,
            headshot_pct=round(avg_hs, 2) if avg_hs is not None else None,
            favorite_heroes_or_agents=list(dict.fromkeys(heroes))[:5],
        )

    async def _persist_classification(
        self,
        user_id: uuid.UUID,
        result: RoleClassificationResult,
        existing_dna: GamerDNA | None,
    ) -> GamerDNA:
        """Saves or updates GamerDNA record with role classification results and raw evaluation payload."""
        now = datetime.now(timezone.utc)
        raw_eval_payload = {
            "confidence_score": result.confidence_score,
            "role_affinities": result.role_affinities,
            "signal_contributions": result.signal_contributions,
            "feature_importance": result.feature_importance,
            "classified_at": now.isoformat(),
        }

        if existing_dna:
            existing_dna.primary_role = result.primary_role
            existing_dna.secondary_role = result.secondary_role
            existing_dna.personality = result.personality
            existing_dna.reasoning = result.reasoning
            existing_dna.raw_evaluation = raw_eval_payload
            existing_dna.updated_at = now
            return await self.dna_repo.update(existing_dna)
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
                primary_role=result.primary_role,
                secondary_role=result.secondary_role,
                personality=result.personality,
                reasoning=result.reasoning,
                raw_evaluation=raw_eval_payload,
                created_at=now,
                updated_at=now,
            )
            return await self.dna_repo.create(new_dna)

    def get_config_metadata(self) -> RoleClassifierConfigResponse:
        """Returns the current classifier configuration metadata and weights."""
        w = self.config.weights
        bm = self.config.benchmarks
        return RoleClassifierConfigResponse(
            supported_roles=self.config.SUPPORTED_ROLES,
            signal_weights={
                "gamer_dna": w.dna_weight,
                "official_stats": w.stats_weight,
                "preferred_roles": w.preferred_roles_weight,
                "preferred_games": w.preferred_games_weight,
            },
            stat_benchmarks={
                "kd_baseline": bm.kd_baseline,
                "kd_elite": bm.kd_elite,
                "win_rate_baseline": bm.win_rate_baseline,
                "win_rate_elite": bm.win_rate_elite,
                "kda_baseline": bm.kda_baseline,
                "min_matches_full_confidence": bm.min_matches_full_confidence,
            },
            role_descriptions=self.config.ROLE_DESCRIPTIONS,
        )
