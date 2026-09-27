"""
Configuration for the AI Explanation Engine.
Defines evaluation thresholds, scoring boundaries, and narrative formatting parameters.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExplanationConfig:
    """Configurable scoring boundaries and formatting limits for explanation generation."""

    # Synergy thresholds
    match_threshold: float = 70.0
    mismatch_threshold: float = 55.0
    high_dimension_threshold: float = 75.0
    low_dimension_threshold: float = 50.0

    # Psychometric thresholds
    clash_leadership_threshold: float = 75.0
    supportive_leadership_threshold: float = 65.0
    silent_comms_threshold: float = 45.0
    high_comms_threshold: float = 75.0
    aggression_delta_threshold: float = 30.0

    # Competitive Telemetry thresholds
    rank_disparity_mmr: int = 400
    win_rate_gap_threshold: float = 12.0

    # Maximum items to include in formatted outputs
    max_match_reasons: int = 4
    max_mismatch_reasons: int = 4
    max_strengths: int = 4
    max_weaknesses: int = 4
    max_suggestions: int = 4


default_explanation_config = ExplanationConfig()
