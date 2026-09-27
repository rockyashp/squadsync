"""
Evaluators for the 5 squad composition dimensions:
1. Compatibility Score
2. Role Balance
3. Skill Balance
4. Communication
5. Leadership Distribution
"""

from collections import Counter
import math
from typing import Sequence

from app.core.squad_recommendation.config import SquadRecommendationConfig, default_squad_config
from app.schemas.matchmaking import MatchmakingCandidate


class RoleBalanceEvaluator:
    """Evaluates coverage of essential tactical roles and detects missing roles."""

    def evaluate(
        self,
        members: Sequence[MatchmakingCandidate],
        config: SquadRecommendationConfig = default_squad_config,
    ) -> tuple[float, dict[str, int], list[str]]:
        """
        Returns (role_balance_score, role_distribution, missing_roles).
        """
        roles = [m.primary_role for m in members]
        role_counts = Counter(roles)

        # Track essential role coverage
        covered = set()
        for r in roles:
            norm_r = r.capitalize()
            if norm_r in config.ESSENTIAL_ROLES:
                covered.add(norm_r)
            elif norm_r == "Leader":
                covered.add("Strategist")  # IGL maps to tactical shotcalling

        missing = [r for r in config.ESSENTIAL_ROLES if r not in covered]

        # Base score from unique essential roles (each role is 20% of 100)
        coverage_score = (len(covered) / len(config.ESSENTIAL_ROLES)) * 100.0

        # Duplicate penalty: having 3+ of the same role penalizes balance
        dupe_penalty = 0.0
        for count in role_counts.values():
            if count >= 3:
                dupe_penalty += 15.0

        final_score = max(20.0, min(100.0, coverage_score - dupe_penalty))
        return round(final_score, 1), dict(role_counts), missing


class SkillBalanceEvaluator:
    """Evaluates competitive parity, average MMR, and skill variance across the squad."""

    def evaluate(
        self,
        members: Sequence[MatchmakingCandidate],
    ) -> tuple[float, float, float]:
        """
        Returns (skill_balance_score, mean_mmr, std_dev).
        """
        if not members:
            return 50.0, 1000.0, 0.0

        mmrs = [m.mmr for m in members]
        mean_mmr = sum(mmrs) / len(mmrs)
        variance = sum((x - mean_mmr) ** 2 for x in mmrs) / len(mmrs)
        std_dev = math.sqrt(variance)

        # Standard deviation penalty: std_dev of 0 -> 100%, 200 -> 60%, 400 -> 20%
        skill_score = max(10.0, min(100.0, 100.0 - (std_dev * 0.20)))
        return round(skill_score, 1), round(mean_mmr, 1), round(std_dev, 1)


class SquadCommunicationEvaluator:
    """Evaluates squad verbal coordination and shared language coherence."""

    def evaluate(
        self,
        members: Sequence[MatchmakingCandidate],
    ) -> float:
        """Computes squad-wide communication score in [0, 100]."""
        if not members:
            return 50.0

        # Average communication trait score
        avg_comms = sum(m.communication for m in members) / len(members)

        # Language commonality check
        if len(members) >= 2:
            shared = set(members[0].languages)
            for m in members[1:]:
                shared = shared.intersection(set(m.languages))
            lang_factor = 1.0 if shared else 0.70
        else:
            lang_factor = 1.0

        final_score = max(20.0, min(100.0, avg_comms * lang_factor))
        return round(final_score, 1)


class LeadershipDistributionEvaluator:
    """
    Evaluates command hierarchy:
    - Exactly 1 dominant shotcaller (>=75) -> 100% (ideal shotcalling structure)
    - 0 dominant shotcallers -> 55% (passive squad, no clear shotcaller)
    - >=2 dominant shotcallers -> 45% (contested calls and ego friction risk)
    """

    def evaluate(
        self,
        members: Sequence[MatchmakingCandidate],
    ) -> tuple[float, str | None, str]:
        """
        Returns (leadership_score, designated_igl_name, assessment).
        """
        leaders = [m for m in members if m.leadership >= 75]

        if len(leaders) == 1:
            igl = leaders[0]
            score = 100.0
            assessment = f"Optimal command hierarchy: {igl.username} serves as dedicated In-Game Leader."
            return score, igl.username, assessment

        elif len(leaders) == 0:
            # Pick highest leadership player as provisional caller
            highest = max(members, key=lambda m: m.leadership) if members else None
            score = 55.0
            igl_name = highest.username if highest else None
            assessment = "No designated vocal shotcaller; team may hesitate on reactive mid-round calls."
            return score, igl_name, assessment

        else:
            score = 45.0
            names = ", ".join(m.username for m in leaders)
            assessment = f"Contested leadership: multiple high-command players ({names}); risk of conflicting shotcalls."
            return score, leaders[0].username, assessment
