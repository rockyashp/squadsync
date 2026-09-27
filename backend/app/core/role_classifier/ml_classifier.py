"""
Machine Learning Classifier Adapter.
Demonstrates the ease of swapping the rule-based classifier with an ML model
(e.g., XGBoost, LightGBM, Random Forest, or PyTorch/ONNX classifier) by implementing
the exact same BaseRoleClassifier contract.
"""

from typing import Any, Sequence

from app.core.role_classifier.base import (
    BaseRoleClassifier,
    RoleClassificationResult,
)
from app.core.role_classifier.config import (
    RoleClassificationConfig,
    default_classification_config,
)
from app.core.role_classifier.engine import RuleBasedRoleClassifier
from app.core.role_classifier.features import GamerRoleFeatures


class MLRoleClassifier(BaseRoleClassifier):
    """
    Drop-in Machine Learning replacement for RuleBasedRoleClassifier.
    Consumes the dense 14-dimensional feature vector extracted from the 4 inputs:
    [DNA traits (6) + In-Game Stats (5) + Preference & Game density (3)].

    Can be initialized with an ONNX runtime session, scikit-learn pipeline, or XGBoost Booster.
    If no pre-trained weights/artifact is passed, it delegates to the rule engine as an
    operational fallback, ensuring zero service downtime.
    """

    def __init__(
        self,
        model_artifact: Any | None = None,
        config: RoleClassificationConfig | None = None,
        classes: Sequence[str] | None = None,
    ) -> None:
        self.model = model_artifact
        self.config = config or default_classification_config
        self.classes = list(classes) if classes is not None else self.config.SUPPORTED_ROLES
        self._fallback_engine = RuleBasedRoleClassifier(config=self.config)

    def classify(self, features: GamerRoleFeatures) -> RoleClassificationResult:
        """
        Runs ML model inference when a model artifact is available,
        otherwise safely falls back to the deterministic rule-based engine.
        """
        # If no serialized model artifact is loaded, use deterministic rule-based fallback
        if self.model is None:
            return self._fallback_engine.classify(features)

        # 1. Extract 14-dimensional dense feature vector
        vector = features.to_dense_vector()

        # 2. Predict probabilities using ML model (e.g. model.predict_proba([vector]))
        if hasattr(self.model, "predict_proba"):
            probs: list[float] = list(self.model.predict_proba([vector])[0])
        elif callable(self.model):
            probs = list(self.model(vector))
        else:
            return self._fallback_engine.classify(features)

        # 3. Map probabilities to role classes
        affinities = {
            role: round(float(prob) * 100.0, 2)
            for role, prob in zip(self.classes, probs)
        }

        # 4. Determine Primary and Secondary roles
        sorted_roles = sorted(affinities.items(), key=lambda item: item[1], reverse=True)
        primary_role, top_score = sorted_roles[0]
        secondary_role, sec_score = sorted_roles[1] if len(sorted_roles) > 1 else (primary_role, top_score)

        # 5. Compute confidence from probability distribution
        top_prob = top_score / 100.0
        sec_prob = sec_score / 100.0
        margin = top_prob - sec_prob
        confidence = round(max(0.30, min(0.99, 0.50 + margin * 0.5)), 4)

        personality = self._fallback_engine._derive_personality(primary_role, secondary_role)

        reasoning = (
            f"PRIMARY ROLE: {primary_role} ({top_score:.1f}% ML confidence). "
            f"Model inference prioritized features from DNA ({features.dna.aggression:.0f} aggression, "
            f"{features.dna.strategy:.0f} strategy) and stats ({features.stats.kd_ratio:.2f} K/D, {features.stats.win_rate:.1f}% WR). "
            f"SECONDARY ROLE: {secondary_role} ({sec_score:.1f}% ML confidence)."
        )

        return RoleClassificationResult(
            primary_role=primary_role,
            secondary_role=secondary_role,
            confidence_score=confidence,
            reasoning=reasoning,
            personality=personality,
            role_affinities=affinities,
            signal_contributions={"ml_model": affinities},
            feature_importance=features.to_feature_dict(),
        )
