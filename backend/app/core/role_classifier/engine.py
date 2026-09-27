"""
Engine implementation for Gamer Role Classification.
Executes rule-based evaluation over multi-signal inputs, computes primary and
secondary roles, calculates mathematically grounded confidence scores, and
synthesizes explainable reasoning.
"""

from collections import defaultdict
import math
from typing import Sequence

from app.core.role_classifier.base import (
    BaseRoleClassifier,
    BaseRoleRule,
    RoleClassificationResult,
    RuleEvaluation,
)
from app.core.role_classifier.config import (
    RoleClassificationConfig,
    default_classification_config,
)
from app.core.role_classifier.features import GamerRoleFeatures
from app.core.role_classifier.rules import (
    ControllerRule,
    DuelistRule,
    LeaderRule,
    SentinelRule,
    StrategistRule,
    SupportRule,
)


class RuleBasedRoleClassifier(BaseRoleClassifier):
    """
    Production rule-based Gamer Role Classification Engine.
    Subclasses BaseRoleClassifier so that it can be transparently substituted
    by an MLRoleClassifier without any alterations to calling services or endpoints.
    """

    def __init__(
        self,
        config: RoleClassificationConfig | None = None,
        rules: Sequence[BaseRoleRule] | None = None,
    ) -> None:
        self.config = config or default_classification_config
        self.rules: list[BaseRoleRule] = list(rules) if rules is not None else [
            LeaderRule(),
            SupportRule(),
            StrategistRule(),
            DuelistRule(),
            SentinelRule(),
            ControllerRule(),
        ]

    def classify(self, features: GamerRoleFeatures) -> RoleClassificationResult:
        """
        Executes classification across:
        1. Gamer DNA feature vector
        2. Official game statistics
        3. Preferred roles
        4. Preferred games
        """
        evaluations: dict[str, RuleEvaluation] = {}
        affinities: dict[str, float] = {}
        signal_contributions: dict[str, dict[str, float]] = {}

        # 1. Evaluate each registered role rule
        for rule in self.rules:
            ev = rule.evaluate(features, self.config)
            evaluations[rule.name] = ev
            affinities[rule.name] = ev.affinity_score
            signal_contributions[rule.name] = {
                "dna": ev.dna_score,
                "stats": ev.stats_score,
                "preference": ev.preference_score,
                "game": ev.game_score,
            }

        # 2. Sort roles descending by affinity
        sorted_roles = sorted(affinities.items(), key=lambda item: item[1], reverse=True)
        primary_role, primary_score = sorted_roles[0]
        secondary_role, secondary_score = sorted_roles[1] if len(sorted_roles) > 1 else (primary_role, primary_score)

        # 3. Calculate Confidence Score
        confidence_score = self._calculate_confidence(
            sorted_roles=sorted_roles,
            evaluations=evaluations,
            features=features,
        )

        # 4. Derive Personality Archetype
        personality = self._derive_personality(primary_role, secondary_role)

        # 5. Synthesize Explainable Reasoning
        reasoning = self._synthesize_reasoning(
            primary_role=primary_role,
            secondary_role=secondary_role,
            evaluations=evaluations,
            features=features,
            confidence_score=confidence_score,
        )

        # 6. Extract Feature Importance snapshot
        feature_importance = self._compute_feature_importance(evaluations[primary_role])

        return RoleClassificationResult(
            primary_role=primary_role,
            secondary_role=secondary_role,
            confidence_score=confidence_score,
            reasoning=reasoning,
            personality=personality,
            role_affinities=affinities,
            signal_contributions=signal_contributions,
            feature_importance=feature_importance,
        )

    def _calculate_confidence(
        self,
        sorted_roles: list[tuple[str, float]],
        evaluations: dict[str, RuleEvaluation],
        features: GamerRoleFeatures,
    ) -> float:
        """
        Computes mathematically grounded confidence score in [0.0, 1.0]:
        - Separation margin: (Score_1 - Score_2) / Score_1
        - Concordance bonus: when DNA trait affinity agrees with Game Stats affinity
        - Preference alignment: when stated preferred roles match primary classification
        - Sample size adjustment: penalized if matches_played is very low
        """
        cfg = self.config.confidence
        top_score = sorted_roles[0][1]
        second_score = sorted_roles[1][1] if len(sorted_roles) > 1 else 0.0

        # Margin component (normalized to ~ 0.35 to 0.75 base)
        margin = (top_score - second_score) / max(top_score, 1.0)
        base_confidence = 0.50 + (margin * cfg.margin_multiplier)

        # Concordance check: inspect if DNA rank 1 matches overall rank 1
        primary_role = sorted_roles[0][0]
        top_dna_role = max(evaluations.items(), key=lambda item: item[1].dna_score)[0]
        top_stats_role = max(evaluations.items(), key=lambda item: item[1].stats_score)[0]

        if top_dna_role == primary_role and top_stats_role == primary_role:
            base_confidence += cfg.concordance_bonus
        elif top_dna_role == primary_role or top_stats_role == primary_role:
            base_confidence += (cfg.concordance_bonus * 0.5)

        # Preference alignment bonus
        pref_matches = any(
            p.strip().lower() in self.config.ROLE_SYNONYMS.get(primary_role, [primary_role.lower()])
            for p in features.preferred_roles
        )
        if pref_matches:
            base_confidence += cfg.preference_alignment_bonus

        # Low sample size dampener
        if features.stats.matches_played < self.config.benchmarks.min_matches_statistical_floor:
            base_confidence -= cfg.low_sample_penalty

        # Clamp between floor and ceiling
        confidence = max(cfg.min_confidence_floor, min(cfg.max_confidence_ceiling, base_confidence))
        return round(confidence, 4)

    def _derive_personality(self, primary: str, secondary: str) -> str:
        """Derives a recognizable competitive gaming persona moniker."""
        archetypes: dict[tuple[str, str], str] = {
            ("Leader", "Strategist"): "The Grandmaster Shotcaller",
            ("Leader", "Duelist"): "The Fearless Vanguard",
            ("Leader", "Support"): "The Inspirational Captain",
            ("Leader", "Controller"): "The Field Marshal",
            ("Leader", "Sentinel"): "The Stalwart Commander",
            ("Strategist", "Leader"): "The Mastermind Tactician",
            ("Strategist", "Controller"): "The Battlefield Architect",
            ("Strategist", "Sentinel"): "The Methodical Watcher",
            ("Strategist", "Support"): "The Analytical Enabler",
            ("Strategist", "Duelist"): "The Calculated Infiltrator",
            ("Duelist", "Leader"): "The Aggressive Warlord",
            ("Duelist", "Strategist"): "The Precision Striker",
            ("Duelist", "Support"): "The Skirmisher Guardian",
            ("Duelist", "Controller"): "The Chaos Catalyst",
            ("Duelist", "Sentinel"): "The Counter-Puncher",
            ("Support", "Sentinel"): "The Aegis Protector",
            ("Support", "Controller"): "The Team Catalyst",
            ("Support", "Leader"): "The Pillar of Morale",
            ("Support", "Strategist"): "The Tactical Lifeline",
            ("Sentinel", "Strategist"): "The Iron Citadel",
            ("Sentinel", "Support"): "The Warden Guardian",
            ("Sentinel", "Controller"): "The Zone Denial Specialist",
            ("Controller", "Strategist"): "The Spatial Puppeteer",
            ("Controller", "Support"): "The Utility Anchor",
            ("Controller", "Duelist"): "The Aggressive Controller",
            ("Controller", "Sentinel"): "The Perimeter Anchor",
        }
        return archetypes.get((primary, secondary), f"The {primary}-{secondary} Specialist")

    def _synthesize_reasoning(
        self,
        primary_role: str,
        secondary_role: str,
        evaluations: dict[str, RuleEvaluation],
        features: GamerRoleFeatures,
        confidence_score: float,
    ) -> str:
        """
        Synthesizes transparent, explainable AI reasoning documenting how
        the 4 input signals converged to yield the assigned roles.
        """
        p_ev = evaluations[primary_role]
        s_ev = evaluations[secondary_role]

        confidence_pct = round(confidence_score * 100.0, 1)

        # Primary rationale
        reasoning_lines = [
            f"PRIMARY ROLE: {primary_role} ({p_ev.affinity_score:.1f}% affinity, {confidence_pct}% model confidence). "
            f"{p_ev.reasoning_snippet}",
            f"SECONDARY ROLE: {secondary_role} ({s_ev.affinity_score:.1f}% affinity). "
            f"{s_ev.reasoning_snippet}",
        ]

        # Input Signal Context
        notes = []
        if features.preferred_roles:
            notes.append(f"Stated role preferences ({', '.join(features.preferred_roles)}) aligned with evaluation.")
        if features.preferred_games:
            notes.append(f"Calibrated for games: {', '.join(features.preferred_games)}.")
        if features.stats.matches_played > 0:
            notes.append(f"Validated across {features.stats.matches_played} recorded matches.")

        if notes:
            reasoning_lines.append("CONTEXT: " + " ".join(notes))

        return " ".join(reasoning_lines)

    def _compute_feature_importance(self, evaluation: RuleEvaluation) -> dict[str, float]:
        """Calculates normalized percentage contribution of each signal towards the primary role."""
        w = self.config.weights
        c_dna = w.dna_weight * evaluation.dna_score
        c_stats = w.stats_weight * evaluation.stats_score
        c_pref = w.preferred_roles_weight * evaluation.preference_score
        c_game = w.preferred_games_weight * evaluation.game_score
        total = max(0.001, c_dna + c_stats + c_pref + c_game)

        return {
            "gamer_dna_influence": round((c_dna / total) * 100.0, 2),
            "game_stats_influence": round((c_stats / total) * 100.0, 2),
            "preferred_roles_influence": round((c_pref / total) * 100.0, 2),
            "preferred_games_influence": round((c_game / total) * 100.0, 2),
        }
