"""
Configuration and weight definitions for the Squad Recommendation Engine.
Balances Compatibility, Role Balance, Skill Balance, Communication, and Leadership Distribution.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SquadRecommendationWeights:
    """
    Relative importance of the 5 squad evaluation criteria.
    Sum equals 1.0 (100%).
    """
    compatibility_weight: float = 0.25
    role_balance_weight: float = 0.25
    skill_balance_weight: float = 0.20
    communication_weight: float = 0.15
    leadership_weight: float = 0.15


class SquadRecommendationConfig:
    """Master configuration for the Squad Recommendation Engine."""

    ESSENTIAL_ROLES: list[str] = [
        "Duelist",
        "Controller",
        "Sentinel",
        "Support",
        "Strategist",
    ]

    def __init__(
        self,
        weights: SquadRecommendationWeights | None = None,
        target_squad_size: int = 5,
        top_teammates_limit: int = 10,
    ) -> None:
        self.weights = weights or SquadRecommendationWeights()
        self.target_squad_size = target_squad_size
        self.top_teammates_limit = top_teammates_limit


default_squad_config = SquadRecommendationConfig()
