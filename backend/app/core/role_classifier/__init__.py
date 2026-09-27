"""
Gamer Role Classification Engine Package.
Exports Configuration, Features, Base Interfaces, Rules, Engine, and ML Adapter.
"""

from app.core.role_classifier.base import (
    BaseRoleClassifier,
    BaseRoleRule,
    RoleClassificationResult,
    RuleEvaluation,
)
from app.core.role_classifier.config import (
    ConfidenceConfig,
    RoleClassificationConfig,
    SignalWeights,
    StatNormalizationBenchmarks,
    default_classification_config,
)
from app.core.role_classifier.engine import RuleBasedRoleClassifier
from app.core.role_classifier.features import (
    GamerDNAVector,
    GamerRoleFeatures,
    OfficialGameStats,
)
from app.core.role_classifier.ml_classifier import MLRoleClassifier
from app.core.role_classifier.rules import (
    ControllerRule,
    DuelistRule,
    LeaderRule,
    SentinelRule,
    StrategistRule,
    SupportRule,
)

__all__ = [
    "BaseRoleClassifier",
    "BaseRoleRule",
    "RoleClassificationResult",
    "RuleEvaluation",
    "SignalWeights",
    "StatNormalizationBenchmarks",
    "ConfidenceConfig",
    "RoleClassificationConfig",
    "default_classification_config",
    "GamerDNAVector",
    "OfficialGameStats",
    "GamerRoleFeatures",
    "RuleBasedRoleClassifier",
    "MLRoleClassifier",
    "LeaderRule",
    "SupportRule",
    "StrategistRule",
    "DuelistRule",
    "SentinelRule",
    "ControllerRule",
]
