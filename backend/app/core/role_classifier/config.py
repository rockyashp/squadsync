"""
Configuration module for the Gamer Role Classification Engine.
Defines signal weights, normalization thresholds, role definitions,
game-specific hero/agent mappings, and confidence score parameters.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SignalWeights:
    """
    Relative importance of the 4 core inputs in rule evaluation:
    1. Gamer DNA (psychometric traits from survey)
    2. Official Game Statistics (telemetry, KD, win rate)
    3. Preferred Roles (stated intent)
    4. Preferred Games (genre context & hero/agent pool)
    Sum should equal 1.0.
    """
    dna_weight: float = 0.40
    stats_weight: float = 0.35
    preferred_roles_weight: float = 0.15
    preferred_games_weight: float = 0.10


@dataclass(frozen=True)
class StatNormalizationBenchmarks:
    """
    Benchmarks used to scale raw in-game stats into bounded [0.0, 1.0] features.
    """
    # Kill/Death Ratio benchmarks
    kd_min: float = 0.5
    kd_baseline: float = 1.0
    kd_high: float = 1.5
    kd_elite: float = 2.2

    # Win rate benchmarks (0.0 to 100.0)
    win_rate_min: float = 30.0
    win_rate_baseline: float = 50.0
    win_rate_high: float = 58.0
    win_rate_elite: float = 70.0

    # Headshot percentage benchmarks (0.0 to 100.0)
    hs_min: float = 5.0
    hs_baseline: float = 18.0
    hs_high: float = 28.0
    hs_elite: float = 42.0

    # KDA benchmarks (K+A)/D
    kda_min: float = 1.0
    kda_baseline: float = 2.0
    kda_high: float = 3.2
    kda_elite: float = 4.5

    # Matches played minimum for full statistical confidence
    min_matches_full_confidence: int = 50
    min_matches_statistical_floor: int = 10


@dataclass(frozen=True)
class ConfidenceConfig:
    """
    Hyperparameters governing confidence score calculation.
    """
    min_confidence_floor: float = 0.25
    max_confidence_ceiling: float = 0.98
    # Margin scaling factor: larger margin between rank 1 and 2 yields higher confidence
    margin_multiplier: float = 0.85
    # Bonus when DNA and Stats both nominate the same top role
    concordance_bonus: float = 0.12
    # Bonus when player's stated preference matches classified primary role
    preference_alignment_bonus: float = 0.08
    # Penalty applied when match sample size is very low (< min_matches_statistical_floor)
    low_sample_penalty: float = 0.15


class RoleClassificationConfig:
    """
    Master configuration singleton for the Gamer Role Classification Engine.
    Provides immutable role lists, archetype matrices, game-to-role mappings,
    and configurable weights.
    """

    SUPPORTED_ROLES: list[str] = [
        "Leader",
        "Support",
        "Strategist",
        "Duelist",
        "Sentinel",
        "Controller",
    ]

    ROLE_DESCRIPTIONS: dict[str, str] = {
        "Leader": "In-Game Leader (IGL) commanding round tempo, shotcalling, and squad composure.",
        "Support": "Selfless enabler prioritizing ally economy, healing, peel, and assist utility.",
        "Strategist": "Tactical architect executing macro rotations, trap setups, and anti-meta counter-play.",
        "Duelist": "Aggressive entry fragger seeking opening engagements and high-velocity space creation.",
        "Sentinel": "Defensive anchor locking down map territory, denying flanks, and delaying enemy pushes.",
        "Controller": "Vision denial and spatial manipulator shaping battlefield sightlines with utility.",
    }

    # Canonical role synonyms for matching user free-form preferences
    ROLE_SYNONYMS: dict[str, list[str]] = {
        "Leader": ["leader", "igl", "shotcaller", "captain", "in-game leader"],
        "Support": ["support", "healer", "hard support", "pos 5", "pos 4", "enabler", "peeler"],
        "Strategist": ["strategist", "tactician", "planner", "macro", "flex", "coach"],
        "Duelist": ["duelist", "entry", "carry", "fragger", "pos 1", "pos 2", "mid", "assassin"],
        "Sentinel": ["sentinel", "anchor", "defender", "offlane", "pos 3", "tank"],
        "Controller": ["controller", "smoker", "vision", "crowd control", "utility"],
    }

    # Preferred Game & Character / Role cross-mapping
    GAME_HERO_AFFINITIES: dict[str, dict[str, list[str]]] = {
        "valorant": {
            "Duelist": ["jett", "reyna", "raze", "phoenix", "yoru", "neon", "iso"],
            "Controller": ["omen", "brimstone", "viper", "astra", "harbor", "clove"],
            "Sentinel": ["killjoy", "cypher", "sage", "deadlock", "chamber"],
            "Strategist": ["sova", "fade", "breach", "skye", "gekko", "tejo", "kayo"],
            "Leader": ["breach", "sova", "omen", "brimstone"],
            "Support": ["skye", "sage", "gekko", "clove"],
        },
        "dota 2": {
            "Duelist": ["anti-mage", "phantom assassin", "juggernaut", "slark", "faceless void", "shadow fiend", "invoker"],
            "Support": ["crystal maiden", "dazzle", "oracle", "witch doctor", "io", "rubick", "lion"],
            "Sentinel": ["tidehunter", "centaur warrunner", "axe", "bristleback", "mars", "slardar"],
            "Strategist": ["puck", "storm spirit", "tinker", "disruptor", "ancient apparition", "invoker"],
            "Controller": ["enigma", "earthshaker", "magnus", "winter wyvern", "dark willow"],
            "Leader": ["treant protector", "chen", "bane", "omniknight"],
        },
        "counter-strike 2": {
            "Duelist": ["entry fragger", "awper", "first contact"],
            "Support": ["flasher", "utility dropper", "trade fragger"],
            "Sentinel": ["b-anchor", "site anchor", "lurker"],
            "Leader": ["igl", "strat caller"],
            "Strategist": ["rotator", "mid control"],
            "Controller": ["smoke executor", "utility coordinator"],
        },
    }

    def __init__(
        self,
        weights: SignalWeights | None = None,
        benchmarks: StatNormalizationBenchmarks | None = None,
        confidence: ConfidenceConfig | None = None,
    ) -> None:
        self.weights = weights or SignalWeights()
        self.benchmarks = benchmarks or StatNormalizationBenchmarks()
        self.confidence = confidence or ConfidenceConfig()


# Default configuration instance
default_classification_config = RoleClassificationConfig()
