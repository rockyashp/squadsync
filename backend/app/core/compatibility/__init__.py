"""
AI Compatibility Engine Package.
Exports Configuration, Models, Evaluators, and Compatibility Engine.
"""

from app.core.compatibility.config import (
    AICompatibilityConfig,
    CompatibilityTier,
    CompatibilityWeights,
    SynergyThresholds,
    default_compatibility_config,
)
from app.core.compatibility.engine import (
    AICompatibilityEngine,
    default_compatibility_engine,
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

__all__ = [
    "CompatibilityTier",
    "CompatibilityWeights",
    "SynergyThresholds",
    "AICompatibilityConfig",
    "default_compatibility_config",
    "PlayerComparisonInput",
    "DimensionScore",
    "CompatibilityReport",
    "PsychometricEvaluator",
    "LogisticsEvaluator",
    "CompetitiveEvaluator",
    "AICompatibilityEngine",
    "default_compatibility_engine",
]
