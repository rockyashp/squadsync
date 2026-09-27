"""
Squad Recommendation Engine.
Calculates Compatibility, Role Balance, Skill Balance, Communication, and Leadership Distribution.
Generates Top 10 Teammates, Best 5-Player Squad, Missing Roles, and Confidence score.
"""

from dataclasses import dataclass, field
import itertools
from typing import Sequence

from app.core.matchmaking.evaluators import CommunicationEvaluator, ScheduleRegionEvaluator, SkillEvaluator, TeamBalanceEvaluator
from app.core.squad_recommendation.config import (
    SquadRecommendationConfig,
    default_squad_config,
)
from app.core.squad_recommendation.evaluators import (
    LeadershipDistributionEvaluator,
    RoleBalanceEvaluator,
    SkillBalanceEvaluator,
    SquadCommunicationEvaluator,
)
from app.schemas.matchmaking import MatchmakingCandidate


@dataclass
class RankedTeammate:
    """Individual candidate ranked by synergy with the current user."""
    user_id: str
    username: str
    compatibility_score: float
    primary_role: str
    secondary_role: str | None
    rank: str
    mmr: int
    win_rate: float
    personality: str
    synergy_highlights: list[str]


@dataclass
class BestSquadOutput:
    """The single optimal 5-player squad composition."""
    overall_score: float
    compatibility_score: float
    role_balance_score: float
    skill_balance_score: float
    communication_score: float
    leadership_score: float
    designated_igl: str | None
    mean_mmr: float
    skill_variance: float
    role_distribution: dict[str, int]
    missing_roles: list[str]
    members: list[MatchmakingCandidate]
    synergy_reasons: list[str]


@dataclass
class SquadRecommendationResult:
    """Consolidated recommendation output."""
    current_user: MatchmakingCandidate
    top_10_teammates: list[RankedTeammate]
    best_5_player_squad: BestSquadOutput
    missing_roles: list[str]
    confidence_score: float
    summary: str


class SquadRecommendationEngine:
    """
    Core engine generating top teammates and the best 5-player squad composition.
    """

    def __init__(self, config: SquadRecommendationConfig | None = None) -> None:
        self.config = config or default_squad_config
        # Evaluators for pairwise synergy
        self.team_balance_eval = TeamBalanceEvaluator()
        self.skill_eval = SkillEvaluator()
        self.comms_eval = CommunicationEvaluator()
        self.sched_reg_eval = ScheduleRegionEvaluator()

        # Evaluators for squad-wide composition
        self.role_evaluator = RoleBalanceEvaluator()
        self.skill_balance_evaluator = SkillBalanceEvaluator()
        self.squad_comms_evaluator = SquadCommunicationEvaluator()
        self.leadership_evaluator = LeadershipDistributionEvaluator()

    def generate_recommendation(
        self,
        current_user: MatchmakingCandidate,
        candidates: Sequence[MatchmakingCandidate],
        game_name: str = "Valorant",
    ) -> SquadRecommendationResult:
        """
        Executes evaluation:
        1. Ranks and extracts Top 10 Teammates.
        2. Combinatorially constructs and selects the Best 5-player squad.
        3. Identifies Missing Roles.
        4. Calculates mathematical Confidence Score.
        """
        # Filter candidate pool to exclude self
        pool = [c for c in candidates if str(c.user_id) != str(current_user.user_id)]

        # 1. Rank all candidates against current user
        ranked_pool = self._rank_individual_candidates(current_user, pool)
        top_10_teammates = ranked_pool[: self.config.top_teammates_limit]

        # 2. Form Best 5-player squad
        best_squad = self._find_best_5_player_squad(current_user, pool, game_name=game_name)

        # 3. Missing roles from the best squad
        missing_roles = best_squad.missing_roles

        # 4. Compute Confidence Score
        confidence_score = self._compute_confidence(
            best_squad=best_squad,
            candidate_pool_size=len(pool),
        )

        # 5. Formulate summary
        missing_text = "All essential roles filled." if not missing_roles else f"Missing tactical roles: {', '.join(missing_roles)}."
        summary = (
            f"Assembled top 5-player squad for {current_user.username} with {best_squad.overall_score:.1f}% overall synergy. "
            f"Role Balance: {best_squad.role_balance_score:.0f}%, Skill Parity: {best_squad.skill_balance_score:.0f}%, "
            f"Communication: {best_squad.communication_score:.0f}%, Leadership: {best_squad.leadership_score:.0f}%. "
            f"{missing_text}"
        )

        return SquadRecommendationResult(
            current_user=current_user,
            top_10_teammates=top_10_teammates,
            best_5_player_squad=best_squad,
            missing_roles=missing_roles,
            confidence_score=confidence_score,
            summary=summary,
        )

    def _evaluate_pair_compatibility(
        self,
        user_a: MatchmakingCandidate,
        user_b: MatchmakingCandidate,
    ) -> tuple[float, list[str]]:
        """Calculates pairwise compatibility percentage between two players."""
        reasons: list[str] = []

        role_s, r_reasons, _ = self.team_balance_eval.evaluate_pair_synergy(user_a, user_b)
        skill_s, s_reasons, _ = self.skill_eval.evaluate_pair(user_a, user_b)
        comm_s, c_reasons, _ = self.comms_eval.evaluate(user_a, user_b)
        sched_s, reg_s, game_s, sr_reasons, _ = self.sched_reg_eval.evaluate(user_a, user_b)

        reasons.extend(r_reasons)
        reasons.extend(s_reasons)
        reasons.extend(c_reasons)

        score = (
            0.25 * role_s
            + 0.20 * skill_s
            + 0.20 * comm_s
            + 0.15 * sched_s
            + 0.10 * reg_s
            + 0.10 * game_s
        )
        return round(max(0.0, min(100.0, score)), 1), reasons

    def _rank_individual_candidates(
        self,
        current_user: MatchmakingCandidate,
        pool: Sequence[MatchmakingCandidate],
    ) -> list[RankedTeammate]:
        """Ranks all pool candidates against Current User by pairwise synergy."""
        ranked: list[RankedTeammate] = []

        for cand in pool:
            compat_score, reasons = self._evaluate_pair_compatibility(current_user, cand)
            ranked.append(
                RankedTeammate(
                    user_id=str(cand.user_id),
                    username=cand.username,
                    compatibility_score=compat_score,
                    primary_role=cand.primary_role,
                    secondary_role=cand.secondary_role,
                    rank=cand.rank or "Unranked",
                    mmr=cand.mmr,
                    win_rate=cand.win_rate,
                    personality=cand.personality or "The Tactical Flexible Player",
                    synergy_highlights=reasons[:3],
                )
            )

        ranked.sort(key=lambda t: t.compatibility_score, reverse=True)
        return ranked

    def _find_best_5_player_squad(
        self,
        current_user: MatchmakingCandidate,
        pool: Sequence[MatchmakingCandidate],
        game_name: str = "Valorant",
    ) -> BestSquadOutput:
        """
        Selects the single best 5-player squad containing Current User + 4 candidates
        optimizing Compatibility, Role Balance, Skill Balance, Communication, and Leadership Distribution.
        """
        target_size = self.config.target_squad_size
        needed_peers = target_size - 1

        if len(pool) < needed_peers:
            # Pool smaller than 4 candidates; return whatever is available
            squad_members = [current_user] + list(pool)
            return self._evaluate_squad_composition(squad_members)

        # Pre-filter candidate pool down to top 16 candidates to keep combinations tractable (C(16, 4) = 1820)
        ranked = self._rank_individual_candidates(current_user, pool)
        top_ids = {t.user_id for t in ranked[:16]}
        focused_pool = [c for c in pool if str(c.user_id) in top_ids]

        best_output: BestSquadOutput | None = None
        best_score = -1.0

        for peers in itertools.combinations(focused_pool, needed_peers):
            combo = [current_user] + list(peers)
            output = self._evaluate_squad_composition(combo)
            if output.overall_score > best_score:
                best_score = output.overall_score
                best_output = output

        return best_output or self._evaluate_squad_composition([current_user] + list(pool[:needed_peers]))

    def _evaluate_squad_composition(
        self,
        members: Sequence[MatchmakingCandidate],
    ) -> BestSquadOutput:
        """Evaluates a 5-player squad across the 5 core dimensions."""
        w = self.config.weights

        # 1. Compatibility Score: average of all pairwise compatibilities
        pairs = list(itertools.combinations(members, 2))
        if pairs:
            pair_scores = [self._evaluate_pair_compatibility(m1, m2)[0] for m1, m2 in pairs]
            compat_score = round(sum(pair_scores) / len(pair_scores), 1)
        else:
            compat_score = 100.0

        # 2. Role Balance & Missing Roles
        role_score, role_dist, missing_roles = self.role_evaluator.evaluate(members, self.config)

        # 3. Skill Balance
        skill_score, mean_mmr, std_dev = self.skill_balance_evaluator.evaluate(members)

        # 4. Squad Communication
        comm_score = self.squad_comms_evaluator.evaluate(members)

        # 5. Leadership Distribution
        lead_score, igl_name, lead_assessment = self.leadership_evaluator.evaluate(members)

        # Weighted Overall Score
        overall = (
            w.compatibility_weight * compat_score
            + w.role_balance_weight * role_score
            + w.skill_balance_weight * skill_score
            + w.communication_weight * comm_score
            + w.leadership_weight * lead_score
        )
        overall_score = round(max(0.0, min(100.0, overall)), 1)

        synergy_reasons = [
            f"Role Balance: {role_score:.0f}% coverage across essential archetypes.",
            f"Skill Parity: {skill_score:.0f}% (Mean MMR: {mean_mmr:.0f}, SD: {std_dev:.1f}).",
            f"Communication: {comm_score:.0f}% squad verbal coordination.",
            lead_assessment,
        ]

        return BestSquadOutput(
            overall_score=overall_score,
            compatibility_score=compat_score,
            role_balance_score=role_score,
            skill_balance_score=skill_score,
            communication_score=comm_score,
            leadership_score=lead_score,
            designated_igl=igl_name,
            mean_mmr=mean_mmr,
            skill_variance=std_dev,
            role_distribution=role_dist,
            missing_roles=missing_roles,
            members=list(members),
            synergy_reasons=synergy_reasons,
        )

    def _compute_confidence(
        self,
        best_squad: BestSquadOutput,
        candidate_pool_size: int,
    ) -> float:
        """
        Computes normalized confidence score in [0.0, 1.0]:
        - Base confidence derived from squad overall score (e.g. 85% -> 0.75 base)
        - Bonus if all essential roles are filled
        - Bonus if dedicated IGL is present
        - Pool depth factor (more candidates to optimize from -> higher confidence)
        """
        base = 0.40 + (best_squad.overall_score / 100.0) * 0.40

        # No missing roles bonus
        if not best_squad.missing_roles:
            base += 0.08

        # Leadership clarity bonus
        if best_squad.leadership_score >= 80.0:
            base += 0.06

        # Pool depth adjustment
        if candidate_pool_size >= 10:
            base += 0.05
        elif candidate_pool_size < 4:
            base -= 0.15

        return round(max(0.20, min(0.98, base)), 4)
