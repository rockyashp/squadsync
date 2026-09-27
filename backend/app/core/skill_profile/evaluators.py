"""
Evaluators for each of the 6 competitive skill dimensions:
- Mechanical Skill
- Communication
- Leadership
- Consistency
- Decision Making
- Game Sense

Fuses Survey behavioral traits, Gamer DNA psychometrics, and official game telemetry
to generate bounded 0-100 scores and transparent, explainable rationales.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.core.role_classifier.features import GamerDNAVector, OfficialGameStats
from app.core.skill_profile.config import (
    SkillBenchmarks,
    SkillProfileConfig,
    default_skill_config,
)


@dataclass(frozen=True)
class SkillDimensionResult:
    """Evaluation result for an individual skill dimension."""
    name: str
    score: float
    tier: str
    explanation: str
    signal_breakdown: dict[str, float]


class BaseSkillEvaluator(ABC):
    """Abstract base evaluator for a single competitive skill dimension."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def evaluate(
        self,
        dna: GamerDNAVector,
        stats: OfficialGameStats,
        config: SkillProfileConfig,
    ) -> SkillDimensionResult:
        """Computes skill score and generates explainable justification."""
        pass

    def _normalize_stat(self, val: float, v_min: float, v_max: float) -> float:
        """Clamps and normalizes a stat value between 0.0 and 1.0."""
        return max(0.0, min(1.0, (val - v_min) / max(0.001, (v_max - v_min))))


class MechanicalSkillEvaluator(BaseSkillEvaluator):
    """
    Evaluates raw mechanical execution: aim precision, lethal conversion,
    headshot percentage, and forward engagement confidence.
    """

    def __init__(self) -> None:
        super().__init__(name="Mechanical Skill")

    def evaluate(
        self,
        dna: GamerDNAVector,
        stats: OfficialGameStats,
        config: SkillProfileConfig,
    ) -> SkillDimensionResult:
        bm = config.benchmarks
        w = config.weights

        # 1. DNA Component: Aggression & Confidence drive mechanical dueling
        dna_score = 0.55 * dna.aggression + 0.45 * dna.confidence

        # 2. Telemetry Component: Headshot % + KD ratio + score per round
        hs_val = stats.headshot_pct if stats.headshot_pct is not None else 18.0
        hs_norm = self._normalize_stat(hs_val, bm.hs_min, bm.hs_max)
        kd_norm = self._normalize_stat(stats.kd_ratio, bm.kd_min, bm.kd_max)
        telemetry_score = (0.50 * hs_norm + 0.50 * kd_norm) * 100.0

        # Weighted blend
        final_score = round(
            w.mechanical_dna_weight * dna_score + w.mechanical_stats_weight * telemetry_score,
            1,
        )
        final_score = max(0.0, min(100.0, final_score))
        tier = config.get_tier(final_score).value

        # Formulate rich, explainable rationale
        hs_phrase = f"{stats.headshot_pct:.1f}% headshot accuracy" if stats.headshot_pct is not None else "measured aim precision"
        explanation = (
            f"Mechanical rating of {final_score}/100 ({tier}) driven by {stats.kd_ratio:.2f} K/D ratio and {hs_phrase}. "
            f"Psychometric aggression ({dna.aggression:.0f}/100) and confidence ({dna.confidence:.0f}/100) corroborate "
            f"strong lethal duel conversion and crisp crosshair control."
        )

        return SkillDimensionResult(
            name=self.name,
            score=final_score,
            tier=tier,
            explanation=explanation,
            signal_breakdown={
                "dna_contribution": round(dna_score, 1),
                "telemetry_contribution": round(telemetry_score, 1),
            },
        )


class CommunicationEvaluator(BaseSkillEvaluator):
    """
    Evaluates situational callouts, voice coordination, utility setup sync,
    and tilt-resistant team communication.
    """

    def __init__(self) -> None:
        super().__init__(name="Communication")

    def evaluate(
        self,
        dna: GamerDNAVector,
        stats: OfficialGameStats,
        config: SkillProfileConfig,
    ) -> SkillDimensionResult:
        bm = config.benchmarks
        w = config.weights

        # 1. DNA Component: Communication & Teamwork
        dna_score = 0.65 * dna.communication + 0.35 * dna.teamwork

        # 2. Telemetry Component: KDA (assists indicate peeling/support) + Win Rate
        kda_norm = self._normalize_stat(stats.kda, bm.kda_min, bm.kda_max)
        wr_norm = self._normalize_stat(stats.win_rate, bm.wr_min, bm.wr_max)
        telemetry_score = (0.60 * kda_norm + 0.40 * wr_norm) * 100.0

        final_score = round(
            w.communication_dna_weight * dna_score + w.communication_stats_weight * telemetry_score,
            1,
        )
        final_score = max(0.0, min(100.0, final_score))
        tier = config.get_tier(final_score).value

        explanation = (
            f"Communication rating of {final_score}/100 ({tier}) reflects survey communication score of "
            f"{dna.communication:.0f}/100 and teamwork of {dna.teamwork:.0f}/100. In-game assist ratio (KDA {stats.kda:.2f}) "
            f"and {stats.win_rate:.1f}% win rate validate active utility synchronization and callout responsiveness."
        )

        return SkillDimensionResult(
            name=self.name,
            score=final_score,
            tier=tier,
            explanation=explanation,
            signal_breakdown={
                "dna_contribution": round(dna_score, 1),
                "telemetry_contribution": round(telemetry_score, 1),
            },
        )


class LeadershipEvaluator(BaseSkillEvaluator):
    """
    Evaluates shotcalling authority, match tempo control, round momentum recovery,
    and squad morale stabilization under clutch pressure.
    """

    def __init__(self) -> None:
        super().__init__(name="Leadership")

    def evaluate(
        self,
        dna: GamerDNAVector,
        stats: OfficialGameStats,
        config: SkillProfileConfig,
    ) -> SkillDimensionResult:
        bm = config.benchmarks
        w = config.weights

        # 1. DNA Component: Leadership & Confidence
        dna_score = 0.65 * dna.leadership + 0.35 * dna.confidence

        # 2. Telemetry Component: Win Rate strongly reflects shotcalling impact
        wr_norm = self._normalize_stat(stats.win_rate, bm.wr_min, bm.wr_max)
        matches_norm = min(1.0, stats.matches_played / bm.min_matches_full_confidence)
        telemetry_score = (0.70 * wr_norm + 0.30 * matches_norm) * 100.0

        final_score = round(
            w.leadership_dna_weight * dna_score + w.leadership_stats_weight * telemetry_score,
            1,
        )
        final_score = max(0.0, min(100.0, final_score))
        tier = config.get_tier(final_score).value

        explanation = (
            f"Leadership rating of {final_score}/100 ({tier}) combines high psychometric leadership ({dna.leadership:.0f}/100) "
            f"with a {stats.win_rate:.1f}% competitive win rate across {stats.matches_played} matches, demonstrating "
            f"consistent macro command and round-stabilizing shotcalling presence."
        )

        return SkillDimensionResult(
            name=self.name,
            score=final_score,
            tier=tier,
            explanation=explanation,
            signal_breakdown={
                "dna_contribution": round(dna_score, 1),
                "telemetry_contribution": round(telemetry_score, 1),
            },
        )


class ConsistencyEvaluator(BaseSkillEvaluator):
    """
    Evaluates round-to-round reliability, match performance stability,
    low tilt susceptibility, and disciplined death avoidance.
    """

    def __init__(self) -> None:
        super().__init__(name="Consistency")

    def evaluate(
        self,
        dna: GamerDNAVector,
        stats: OfficialGameStats,
        config: SkillProfileConfig,
    ) -> SkillDimensionResult:
        bm = config.benchmarks
        w = config.weights

        # 1. DNA Component: Disciplined teamwork + measured aggression
        dna_score = 0.50 * dna.teamwork + 0.30 * dna.strategy + 0.20 * max(0.0, 100.0 - abs(dna.aggression - 50.0))

        # 2. Telemetry Component: Match sample confidence + KD stability + Win Rate
        matches_factor = min(1.0, stats.matches_played / bm.min_matches_full_confidence)
        wr_norm = self._normalize_stat(stats.win_rate, bm.wr_min, bm.wr_max)
        kd_norm = self._normalize_stat(stats.kd_ratio, bm.kd_min, bm.kd_max)
        telemetry_score = (0.45 * matches_factor + 0.30 * wr_norm + 0.25 * kd_norm) * 100.0

        final_score = round(
            w.consistency_dna_weight * dna_score + w.consistency_stats_weight * telemetry_score,
            1,
        )
        final_score = max(0.0, min(100.0, final_score))
        tier = config.get_tier(final_score).value

        sample_note = f"a solid sample of {stats.matches_played} games" if stats.matches_played >= 20 else f"an emerging baseline of {stats.matches_played} games"
        explanation = (
            f"Consistency score of {final_score}/100 ({tier}) established across {sample_note}. "
            f"Low performance volatility is anchored by disciplined teamwork ({dna.teamwork:.0f}/100) and steady "
            f"{stats.kd_ratio:.2f} K/D trade conversion."
        )

        return SkillDimensionResult(
            name=self.name,
            score=final_score,
            tier=tier,
            explanation=explanation,
            signal_breakdown={
                "dna_contribution": round(dna_score, 1),
                "telemetry_contribution": round(telemetry_score, 1),
            },
        )


class DecisionMakingEvaluator(BaseSkillEvaluator):
    """
    Evaluates situational judgment, trade fragging awareness, risk-reward assessment,
    eco round discipline, and minimizing unforced errors.
    """

    def __init__(self) -> None:
        super().__init__(name="Decision Making")

    def evaluate(
        self,
        dna: GamerDNAVector,
        stats: OfficialGameStats,
        config: SkillProfileConfig,
    ) -> SkillDimensionResult:
        bm = config.benchmarks
        w = config.weights

        # 1. DNA Component: Strategy & Teamwork
        dna_score = 0.60 * dna.strategy + 0.40 * dna.teamwork

        # 2. Telemetry Component: KDA (high assist-to-death ratio shows calculated risks) + Win Rate
        kda_norm = self._normalize_stat(stats.kda, bm.kda_min, bm.kda_max)
        wr_norm = self._normalize_stat(stats.win_rate, bm.wr_min, bm.wr_max)
        kd_norm = self._normalize_stat(stats.kd_ratio, bm.kd_min, bm.kd_max)
        telemetry_score = (0.50 * kda_norm + 0.30 * wr_norm + 0.20 * kd_norm) * 100.0

        final_score = round(
            w.decision_making_dna_weight * dna_score + w.decision_making_stats_weight * telemetry_score,
            1,
        )
        final_score = max(0.0, min(100.0, final_score))
        tier = config.get_tier(final_score).value

        explanation = (
            f"Decision Making rating of {final_score}/100 ({tier}) grounded in strategic psychometrics ({dna.strategy:.0f}/100) "
            f"and calculated trade efficiency (KDA {stats.kda:.2f}). Indicates disciplined engagement timing and favorable "
            f"risk-reward choices during high-leverage rounds."
        )

        return SkillDimensionResult(
            name=self.name,
            score=final_score,
            tier=tier,
            explanation=explanation,
            signal_breakdown={
                "dna_contribution": round(dna_score, 1),
                "telemetry_contribution": round(telemetry_score, 1),
            },
        )


class GameSenseEvaluator(BaseSkillEvaluator):
    """
    Evaluates macro map awareness, anticipation of enemy rotations, vision control,
    flank denial, and objective timing.
    """

    def __init__(self) -> None:
        super().__init__(name="Game Sense")

    def evaluate(
        self,
        dna: GamerDNAVector,
        stats: OfficialGameStats,
        config: SkillProfileConfig,
    ) -> SkillDimensionResult:
        bm = config.benchmarks
        w = config.weights

        # 1. DNA Component: Strategy, Comms, and Leadership
        dna_score = 0.50 * dna.strategy + 0.30 * dna.communication + 0.20 * dna.leadership

        # 2. Telemetry Component: Win rate + KD + KDA
        wr_norm = self._normalize_stat(stats.win_rate, bm.wr_min, bm.wr_max)
        kd_norm = self._normalize_stat(stats.kd_ratio, bm.kd_min, bm.kd_max)
        kda_norm = self._normalize_stat(stats.kda, bm.kda_min, bm.kda_max)
        telemetry_score = (0.45 * wr_norm + 0.35 * kd_norm + 0.20 * kda_norm) * 100.0

        final_score = round(
            w.game_sense_dna_weight * dna_score + w.game_sense_stats_weight * telemetry_score,
            1,
        )
        final_score = max(0.0, min(100.0, final_score))
        tier = config.get_tier(final_score).value

        explanation = (
            f"Game Sense score of {final_score}/100 ({tier}) derived from macro strategy ({dna.strategy:.0f}/100) and communication "
            f"({dna.communication:.0f}/100). Validated by consistent competitive win rate ({stats.win_rate:.1f}%), indicating "
            f"adept spatial anticipation and enemy rotation reads."
        )

        return SkillDimensionResult(
            name=self.name,
            score=final_score,
            tier=tier,
            explanation=explanation,
            signal_breakdown={
                "dna_contribution": round(dna_score, 1),
                "telemetry_contribution": round(telemetry_score, 1),
            },
        )
