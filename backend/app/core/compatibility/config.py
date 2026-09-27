"""
Configuration, weights, tier thresholds, and risk criteria for the AI Compatibility Engine.
Defines relative weights across the 10 comparison dimensions:
- Leadership
- Communication
- Aggression
- Strategy
- Region
- Language
- Schedule
- Official Rank
- Win Rate
- Preferred Role
"""

from dataclasses import dataclass, field
from enum import Enum


class CompatibilityTier(str, Enum):
    """Qualitative compatibility tier classifications."""
    OPTIMAL = "Optimal Duo Synergy (90-100%)"
    STRONG = "Strong Compatibility (75-89%)"
    MODERATE = "Moderate Synergy (60-74%)"
    QUESTIONABLE = "Questionable Alignment (45-59%)"
    HIGH_RISK = "High Friction Risk (<45%)"


@dataclass(frozen=True)
class CompatibilityWeights:
    """
    Normalized weights for the 10 comparison dimensions.
    Sum equals 1.0 (100%).
    """
    # Psychometrics (DNA) - 42%
    leadership_weight: float = 0.10
    communication_weight: float = 0.12
    aggression_weight: float = 0.10
    strategy_weight: float = 0.10

    # Logistics - 28%
    region_weight: float = 0.10
    language_weight: float = 0.10
    schedule_weight: float = 0.08

    # Competitive Telemetry - 30%
    rank_weight: float = 0.10
    win_rate_weight: float = 0.08
    role_weight: float = 0.12


@dataclass(frozen=True)
class SynergyThresholds:
    """Threshold constants for identifying strengths, weaknesses, and risk factors."""
    # Dual leadership clash threshold
    high_leadership_threshold: float = 75.0
    low_leadership_threshold: float = 55.0

    # Rank disparity threshold (normalized MMR difference)
    max_rank_disparity_allowed: float = 25.0  # Equivalent to ~1 full skill tier

    # Win rate disparity threshold
    max_win_rate_disparity: float = 12.0

    # High synergy cutoff for strengths
    strength_cutoff: float = 80.0

    # Low synergy cutoff for weaknesses
    weakness_cutoff: float = 50.0


class AICompatibilityConfig:
    """Master configuration container for the AI Compatibility Engine."""

    def __init__(
        self,
        weights: CompatibilityWeights | None = None,
        thresholds: SynergyThresholds | None = None,
    ) -> None:
        self.weights = weights or CompatibilityWeights()
        self.thresholds = thresholds or SynergyThresholds()

    @staticmethod
    def get_tier(score: float) -> CompatibilityTier:
        """Categorizes compatibility score into qualitative tier."""
        if score >= 90.0:
            return CompatibilityTier.OPTIMAL
        elif score >= 75.0:
            return CompatibilityTier.STRONG
        elif score >= 60.0:
            return CompatibilityTier.MODERATE
        elif score >= 45.0:
            return CompatibilityTier.QUESTIONABLE
        return CompatibilityTier.HIGH_RISK


default_compatibility_config = AICompatibilityConfig()
