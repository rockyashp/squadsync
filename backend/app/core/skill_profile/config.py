"""
Configuration, benchmarks, and tier mapping for the Skill Profile Generator.
Defines weight balances and performance thresholds for the 6 skill dimensions:
- Mechanical Skill
- Communication
- Leadership
- Consistency
- Decision Making
- Game Sense
"""

from dataclasses import dataclass, field
from enum import Enum


class SkillTier(str, Enum):
    """Competitive skill tier classifications."""
    S_TIER = "S-Tier (Elite)"
    A_TIER = "A-Tier (Advanced)"
    B_TIER = "B-Tier (Proficient)"
    C_TIER = "C-Tier (Developing)"
    D_TIER = "D-Tier (Novice)"


@dataclass(frozen=True)
class DimensionWeights:
    """
    Weights balancing Survey/DNA psychometrics vs. Official telemetry per skill dimension.
    """
    # Mechanical Skill: telemetry (headshots, KD) dominates
    mechanical_dna_weight: float = 0.40
    mechanical_stats_weight: float = 0.60

    # Communication: survey communication & teamwork + assist conversion
    communication_dna_weight: float = 0.55
    communication_stats_weight: float = 0.45

    # Leadership: survey leadership & shotcalling + competitive win rate
    leadership_dna_weight: float = 0.50
    leadership_stats_weight: float = 0.50

    # Consistency: low variance across matches + sample size
    consistency_dna_weight: float = 0.35
    consistency_stats_weight: float = 0.65

    # Decision Making: strategy + survivability & trade efficiency
    decision_making_dna_weight: float = 0.45
    decision_making_stats_weight: float = 0.55

    # Game Sense: strategy + macro rank benchmark & tactical win rate
    game_sense_dna_weight: float = 0.45
    game_sense_stats_weight: float = 0.55


@dataclass(frozen=True)
class SkillBenchmarks:
    """
    Normalization benchmarks for scaling raw telemetry into 0-100 skill scores.
    """
    kd_min: float = 0.5
    kd_max: float = 2.2

    hs_min: float = 5.0
    hs_max: float = 40.0

    wr_min: float = 35.0
    wr_max: float = 68.0

    kda_min: float = 1.0
    kda_max: float = 4.2

    min_matches_full_confidence: int = 50


class SkillProfileConfig:
    """Configuration singleton for skill evaluation."""

    def __init__(
        self,
        weights: DimensionWeights | None = None,
        benchmarks: SkillBenchmarks | None = None,
    ) -> None:
        self.weights = weights or DimensionWeights()
        self.benchmarks = benchmarks or SkillBenchmarks()

    @staticmethod
    def get_tier(score: float) -> SkillTier:
        """Assigns qualitative tier to numerical score (0 to 100)."""
        if score >= 85.0:
            return SkillTier.S_TIER
        elif score >= 70.0:
            return SkillTier.A_TIER
        elif score >= 55.0:
            return SkillTier.B_TIER
        elif score >= 40.0:
            return SkillTier.C_TIER
        return SkillTier.D_TIER


default_skill_config = SkillProfileConfig()
