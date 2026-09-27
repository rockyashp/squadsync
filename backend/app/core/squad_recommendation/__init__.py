"""
Squad Recommendation Package.
Exports Engine, Evaluators, and Configurations.
"""

from app.core.squad_recommendation.config import (
    SquadRecommendationConfig,
    SquadRecommendationWeights,
    default_squad_config,
)
from app.core.squad_recommendation.engine import (
    BestSquadOutput,
    RankedTeammate,
    SquadRecommendationEngine,
    SquadRecommendationResult,
)
from app.core.squad_recommendation.evaluators import (
    LeadershipDistributionEvaluator,
    RoleBalanceEvaluator,
    SkillBalanceEvaluator,
    SquadCommunicationEvaluator,
)

__all__ = [
    "SquadRecommendationWeights",
    "SquadRecommendationConfig",
    "default_squad_config",
    "RankedTeammate",
    "BestSquadOutput",
    "SquadRecommendationResult",
    "RoleBalanceEvaluator",
    "SkillBalanceEvaluator",
    "SquadCommunicationEvaluator",
    "LeadershipDistributionEvaluator",
    "SquadRecommendationEngine",
]
