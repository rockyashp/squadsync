"""
Matchmaking Engine and Combinatorial Squad Optimizer.
Coordinates specialized evaluators to calculate pairwise compatibility %, reasons, warnings,
and selects optimal squad compositions.
"""

from collections import Counter
import itertools
from typing import Sequence

from app.core.matchmaking.evaluators import (
    CommunicationEvaluator,
    ScheduleRegionEvaluator,
    SkillEvaluator,
    TeamBalanceEvaluator,
)
from app.schemas.matchmaking import (
    CompatibilityResponse,
    MatchmakingCandidate,
    PairwiseCompatibilityBreakdown,
    SquadComposition,
    SquadMember,
)


class MatchmakingEngine:
    """Core engine calculating multi-dimensional player and squad compatibility."""

    def __init__(self) -> None:
        self.skill_evaluator = SkillEvaluator()
        self.balance_evaluator = TeamBalanceEvaluator()
        self.comms_evaluator = CommunicationEvaluator()
        self.schedule_region_evaluator = ScheduleRegionEvaluator()

    def evaluate_pair(
        self,
        player_a: MatchmakingCandidate,
        player_b: MatchmakingCandidate,
    ) -> CompatibilityResponse:
        """Computes granular 7-dimension compatibility breakdown between two players."""
        reasons: list[str] = []
        warnings: list[str] = []

        # 1. Role Synergy
        role_score, r_reasons, r_warns = self.balance_evaluator.evaluate_pair_synergy(player_a, player_b)
        reasons.extend(r_reasons)
        warnings.extend(r_warns)

        # 2. Skill Alignment
        skill_score, s_reasons, s_warns = self.skill_evaluator.evaluate_pair(player_a, player_b)
        reasons.extend(s_reasons)
        warnings.extend(s_warns)

        # 3. Communication & Language Match
        comm_score, c_reasons, c_warns = self.comms_evaluator.evaluate(player_a, player_b)
        reasons.extend(c_reasons)
        warnings.extend(c_warns)

        # Language sub-score
        shared_langs = set(player_a.languages).intersection(set(player_b.languages))
        lang_score = 100.0 if shared_langs else 20.0

        # 4. Schedule, Region, and Games Match
        sched_score, reg_score, game_score, sr_reasons, sr_warns = self.schedule_region_evaluator.evaluate(player_a, player_b)
        reasons.extend(sr_reasons)
        warnings.extend(sr_warns)

        # Weighted composite compatibility percentage
        weights = {
            "role": 0.25,
            "skill": 0.20,
            "comm": 0.20,
            "sched": 0.15,
            "lang": 0.10,
            "region": 0.10,
        }
        overall = (
            role_score * weights["role"]
            + skill_score * weights["skill"]
            + comm_score * weights["comm"]
            + sched_score * weights["sched"]
            + lang_score * weights["lang"]
            + reg_score * weights["region"]
        )

        overall_pct = round(max(0.0, min(100.0, overall)), 1)

        breakdown = PairwiseCompatibilityBreakdown(
            role_synergy=role_score,
            communication_match=comm_score,
            skill_alignment=skill_score,
            schedule_overlap=sched_score,
            language_match=lang_score,
            region_match=reg_score,
            game_match=game_score,
        )

        return CompatibilityResponse(
            player_a_id=player_a.user_id,
            player_b_id=player_b.user_id,
            player_a_username=player_a.username,
            player_b_username=player_b.username,
            overall_compatibility_pct=overall_pct,
            breakdown=breakdown,
            reasons=list(dict.fromkeys(reasons))[:5],  # Deduplicate and keep top 5
            warnings=list(dict.fromkeys(warnings))[:4],
        )

    def evaluate_squad(
        self,
        members: Sequence[MatchmakingCandidate],
        game_name: str = "Valorant",
        target_size: int = 5,
    ) -> SquadComposition:
        """Analyzes full squad synergy, team balance, missing roles, skill variance, and warnings."""
        if not members:
            raise ValueError("Members list cannot be empty.")

        reasons: list[str] = []
        warnings: list[str] = []

        # 1. Team Balance & Missing Roles
        balance_pct, role_distribution, missing_roles, b_reasons, b_warns = (
            self.balance_evaluator.evaluate_squad_composition(members, target_size=target_size)
        )
        reasons.extend(b_reasons)
        warnings.extend(b_warns)

        # 2. Skill Variance
        std_dev, s_reasons, s_warns = self.skill_evaluator.evaluate_squad_variance(members)
        reasons.extend(s_reasons)
        warnings.extend(s_warns)

        # 3. Pairwise compatibility across all squad edges
        pairs = list(itertools.combinations(members, 2))
        pairwise_compatibilities: list[float] = []
        comms_scores: list[float] = []

        for p_a, p_b in pairs:
            pair_res = self.evaluate_pair(p_a, p_b)
            pairwise_compatibilities.append(pair_res.overall_compatibility_pct)
            comms_scores.append(pair_res.breakdown.communication_match)

        avg_compat = sum(pairwise_compatibilities) / len(pairwise_compatibilities) if pairwise_compatibilities else 75.0
        avg_comms = sum(comms_scores) / len(comms_scores) if comms_scores else 75.0

        # Overall squad synergy blends balance and pairwise compatibility
        squad_compat = round(0.50 * balance_pct + 0.35 * avg_compat + 0.15 * avg_comms, 1)

        # Build SquadMember models
        squad_members = [
            SquadMember(
                user_id=m.user_id,
                username=m.username,
                assigned_role=m.primary_role,
                primary_role=m.primary_role,
                secondary_role=m.secondary_role,
                rank=m.rank,
                mmr=m.mmr,
                win_rate=m.win_rate,
                personality=m.personality,
            )
            for m in members
        ]

        return SquadComposition(
            squad_size=len(members),
            game_name=game_name,
            members=squad_members,
            compatibility_pct=squad_compat,
            team_balance_pct=balance_pct,
            communication_match_pct=round(avg_comms, 1),
            skill_variance=std_dev,
            role_distribution=role_distribution,
            missing_roles=missing_roles,
            reasons=list(dict.fromkeys(reasons))[:6],
            warnings=list(dict.fromkeys(warnings))[:5],
        )


class SquadOptimizer:
    """Heuristic combinatorial optimizer that selects the top recommended squads from candidates."""

    def __init__(self, engine: MatchmakingEngine | None = None) -> None:
        self.engine = engine or MatchmakingEngine()

    def recommend_squads(
        self,
        requester: MatchmakingCandidate,
        candidates: Sequence[MatchmakingCandidate],
        game_name: str = "Valorant",
        squad_size: int = 5,
        top_k: int = 3,
    ) -> list[SquadComposition]:
        """
        Forms candidate squads of size `squad_size` containing `requester` and evaluates them.
        Returns top `top_k` squads ranked by overall compatibility and balance.
        """
        pool = [c for c in candidates if c.user_id != requester.user_id]
        if len(pool) < (squad_size - 1):
            # Not enough candidates to form full squad; evaluate whatever pool is available
            combo = [requester] + pool
            return [self.engine.evaluate_squad(combo, game_name=game_name, target_size=squad_size)]

        # Pre-filter candidates: prioritize same/adjacent region and shared game
        scored_pool = []
        for c in pool:
            # Quick suitability score
            score = 0.0
            if c.region.lower() == requester.region.lower():
                score += 30.0
            if game_name in c.preferred_games:
                score += 30.0
            if abs(c.mmr - requester.mmr) <= 400:
                score += 25.0
            if set(c.languages).intersection(set(requester.languages)):
                score += 15.0
            scored_pool.append((score, c))

        # Take top candidates for combinatorial evaluation to manage complexity
        scored_pool.sort(key=lambda x: x[0], reverse=True)
        top_candidates = [item[1] for item in scored_pool[:18]]

        needed_peers = squad_size - 1
        evaluated_squads: list[SquadComposition] = []

        # Evaluate combinatorial subsets
        for peers in itertools.combinations(top_candidates, needed_peers):
            candidate_squad = [requester] + list(peers)
            composition = self.engine.evaluate_squad(
                candidate_squad,
                game_name=game_name,
                target_size=squad_size,
            )
            evaluated_squads.append(composition)

        # Sort squads by compatibility_pct descending, then by team_balance_pct descending
        evaluated_squads.sort(
            key=lambda s: (s.compatibility_pct, s.team_balance_pct, -s.skill_variance),
            reverse=True,
        )

        return evaluated_squads[:top_k]
