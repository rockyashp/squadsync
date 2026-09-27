"""
AI Compatibility Engine.
Orchestrates comparison across 10 dimensions, evaluates weighted compatibility score,
and derives actionable Strengths, Weaknesses, Recommendations, and Risk Factors.
"""

from app.core.compatibility.config import (
    AICompatibilityConfig,
    default_compatibility_config,
)
from app.core.compatibility.evaluators import (
    CompetitiveEvaluator,
    LogisticsEvaluator,
    PsychometricEvaluator,
)
from app.core.compatibility.models import (
    CompatibilityReport,
    DimensionScore,
    PlayerComparisonInput,
)


class AICompatibilityEngine:
    """
    AI Compatibility Engine computing multi-dimensional duo synergy,
    risk factors, and tactical teaming guidance.
    """

    def __init__(self, config: AICompatibilityConfig | None = None) -> None:
        self.config = config or default_compatibility_config
        self.psychometric_evaluator = PsychometricEvaluator()
        self.logistics_evaluator = LogisticsEvaluator()
        self.competitive_evaluator = CompetitiveEvaluator()

    def compare(
        self,
        player_a: PlayerComparisonInput,
        player_b: PlayerComparisonInput,
    ) -> CompatibilityReport:
        """
        Executes pairwise comparison across the 10 dimensions and synthesizes the full report.
        """
        # 1. Evaluate all dimensions
        dimension_scores: list[DimensionScore] = []
        dimension_scores.extend(self.psychometric_evaluator.evaluate(player_a, player_b, self.config))
        dimension_scores.extend(self.logistics_evaluator.evaluate(player_a, player_b, self.config))
        dimension_scores.extend(self.competitive_evaluator.evaluate(player_a, player_b, self.config))

        dim_map = {d.dimension: d for d in dimension_scores}
        score_dict = {d.dimension: d.score for d in dimension_scores}

        # 2. Compute Weighted Compatibility Score
        weighted_total = sum(d.score * d.weight for d in dimension_scores)
        total_weight = sum(d.weight for d in dimension_scores)
        normalized_score = round(max(0.0, min(100.0, weighted_total / max(0.001, total_weight))), 1)

        # 3. Determine Tier
        tier = self.config.get_tier(normalized_score).value

        # 4. Synthesize Strengths, Weaknesses, Risk Factors, and Recommendations
        strengths = self._derive_strengths(dimension_scores, player_a, player_b)
        weaknesses = self._derive_weaknesses(dimension_scores, player_a, player_b)
        risk_factors = self._detect_risk_factors(dimension_scores, player_a, player_b)
        recommendations = self._formulate_recommendations(dimension_scores, player_a, player_b)

        return CompatibilityReport(
            player_a_name=player_a.username,
            player_b_name=player_b.username,
            compatibility_score=normalized_score,
            tier=tier,
            dimension_scores=score_dict,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            risk_factors=risk_factors,
        )

    def _derive_strengths(
        self,
        dimensions: list[DimensionScore],
        player_a: PlayerComparisonInput,
        player_b: PlayerComparisonInput,
    ) -> list[str]:
        """Identifies synergistic highlights where players complement each other."""
        strengths: list[str] = []
        th = self.config.thresholds

        high_dims = [d for d in dimensions if d.score >= th.strength_cutoff]
        for d in high_dims:
            strengths.append(f"{d.dimension} ({d.score:.0f}/100): {d.assessment}")

        # Guarantee at least 2 strengths
        if len(strengths) < 2:
            sorted_dims = sorted(dimensions, key=lambda d: d.score, reverse=True)
            for d in sorted_dims:
                phrase = f"{d.dimension} Synergy: {d.assessment}"
                if phrase not in strengths:
                    strengths.append(phrase)
                if len(strengths) >= 2:
                    break

        return strengths[:4]

    def _derive_weaknesses(
        self,
        dimensions: list[DimensionScore],
        player_a: PlayerComparisonInput,
        player_b: PlayerComparisonInput,
    ) -> list[str]:
        """Identifies friction points or areas of sub-optimal alignment."""
        weaknesses: list[str] = []
        th = self.config.thresholds

        low_dims = [d for d in dimensions if d.score < th.weakness_cutoff]
        for d in low_dims:
            weaknesses.append(f"{d.dimension} Friction ({d.score:.0f}/100): {d.assessment}")

        # If no severe weaknesses, highlight lowest scoring areas constructively
        if not weaknesses:
            sorted_dims = sorted(dimensions, key=lambda d: d.score)
            for d in sorted_dims[:2]:
                if d.score < 80.0:
                    weaknesses.append(f"{d.dimension} ({d.score:.0f}/100): Minor divergence in {d.dimension.lower()} preferences.")

        return weaknesses[:4]

    def _detect_risk_factors(
        self,
        dimensions: list[DimensionScore],
        player_a: PlayerComparisonInput,
        player_b: PlayerComparisonInput,
    ) -> list[str]:
        """Flags critical compatibility warnings and co-op blockers."""
        risks: list[str] = []
        dim_map = {d.dimension: d for d in dimensions}

        # 1. Dual leadership clash
        if player_a.leadership >= 75.0 and player_b.leadership >= 75.0:
            risks.append(
                "DUAL SHOTCALLER CONFLICT: Both players have dominant leadership ratings (75+), "
                "which may cause contested mid-round shotcalls and tactical friction."
            )

        # 2. Language barrier
        if dim_map["Language"].score <= 20.0:
            risks.append(
                "CRITICAL LANGUAGE BARRIER: No shared fluent language detected. "
                "Voice communication will be severely limited during fast engagements."
            )

        # 3. Server latency / cross-region
        if dim_map["Region"].score <= 30.0:
            risks.append(
                f"HIGH LATENCY PENALTY: Significant regional distance between {player_a.region} and "
                f"{player_b.region}. One or both players will experience elevated server ping."
            )

        # 4. Rank disparity
        if abs(player_a.rank_rating - player_b.rank_rating) >= 500:
            risks.append(
                f"RANK DISPARITY WARNING: {abs(player_a.rank_rating - player_b.rank_rating)} MMR difference. "
                "May trigger competitive lobby party restrictions or high skill variance."
            )

        # 5. Direct role clash
        if dim_map["Preferred Role"].score <= 35.0:
            risks.append(
                "ROLE COLLISION: Both players prefer the exact same primary tactical role with low flex overlap. "
                "Pre-match agent/hero assignment required to prevent tilt."
            )

        # 6. Win rate gap
        if abs(player_a.win_rate - player_b.win_rate) >= 15.0:
            risks.append(
                f"WIN RATE DISCREPANCY: Large competitive win-rate gap ({player_a.win_rate:.1f}% vs. {player_b.win_rate:.1f}%), "
                "creating vulnerability to frustration during losing streaks."
            )

        return risks

    def _formulate_recommendations(
        self,
        dimensions: list[DimensionScore],
        player_a: PlayerComparisonInput,
        player_b: PlayerComparisonInput,
    ) -> list[str]:
        """Provides actionable teaming recommendations and duo playstyle advice."""
        recs: list[str] = []
        dim_map = {d.dimension: d for d in dimensions}

        # Role & In-Game Dynamic
        if player_a.leadership > player_b.leadership:
            recs.append(
                f"Tactical Shotcalling: Designate {player_a.username} as the primary In-Game Leader (IGL) "
                f"for site hit calls, while {player_b.username} provides information callouts."
            )
        elif player_b.leadership > player_a.leadership:
            recs.append(
                f"Tactical Shotcalling: Designate {player_b.username} as the primary In-Game Leader (IGL), "
                f"with {player_a.username} executing second-contact entry."
            )
        else:
            recs.append(
                "Co-Calling Protocol: Pre-agree on attack calls during buy-phase to prevent conflicting mid-round decisions."
            )

        # Engagement Pacing
        if player_a.aggression >= 70.0 and player_b.aggression < 60.0:
            recs.append(
                f"Pacing Synergy: Position {player_a.username} on opening duel contact while {player_b.username} "
                f"follows closely within trade distance (1-2 seconds) to guarantee the re-frag."
            )
        elif player_b.aggression >= 70.0 and player_a.aggression < 60.0:
            recs.append(
                f"Pacing Synergy: Have {player_b.username} initiate first contact while {player_a.username} "
                f"provides backline cover fire and utility support."
            )
        else:
            recs.append(
                "Crossfire Setup: Hold coordinated crossfire angles rather than stacked angles on defensive rounds."
            )

        # Communication Protocol
        if dim_map["Communication"].score < 70.0:
            recs.append(
                "Communication Protocol: Rely heavily on in-game visual ping markers and standard damage callouts "
                "('Tag 120 Lit') to streamline information transfer."
            )
        else:
            recs.append(
                "Advanced Communication: Coordinate synchronized double-peeks and combo utility (e.g. flash + smoke deploy)."
            )

        # Logistics
        if dim_map["Schedule"].score < 60.0:
            recs.append(
                "Scheduling Alignment: Set a recurring weekly play window to maximize queue consistency."
            )

        return recs[:4]


default_compatibility_engine = AICompatibilityEngine()
