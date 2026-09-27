"""
Rule-Based Gamer Role Classification Engine.
Calculates psychometric category scores from survey responses and classifies
gamers into Primary and Secondary roles:
- Leader
- Support
- Strategist
- Duelist
- Sentinel
- Controller
"""

from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Sequence

from app.models.survey_response import SurveyResponse


@dataclass(frozen=True)
class ClassificationResult:
    """Encapsulates output of the rule-based classification engine."""
    primary_role: str
    secondary_role: str
    personality: str
    scores: dict[str, int]
    role_affinities: dict[str, float]
    reasoning: str


class BaseRoleRule(ABC):
    """
    Extensible rule base class for defining gamer roles.
    To add a new role in the future, simply subclass BaseRoleRule and register it.
    """

    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description

    @abstractmethod
    def calculate_affinity(self, scores: dict[str, int]) -> float:
        """Calculate numerical affinity score (0-100) for this role given category scores."""
        pass

    @abstractmethod
    def get_reasoning(self, scores: dict[str, int]) -> str:
        """Generate human-readable justification for this role assignment."""
        pass


class LeaderRule(BaseRoleRule):
    """Leader: High Leadership, Communication, and decisive tactical direction."""

    def __init__(self) -> None:
        super().__init__(
            name="Leader",
            description="Commands the match tempo, inspires squad confidence, and shotcalls during high-pressure rounds.",
        )

    def calculate_affinity(self, scores: dict[str, int]) -> float:
        l = scores.get("Leadership", 0)
        c = scores.get("Communication", 0)
        s = scores.get("Strategy", 0)
        return round(0.50 * l + 0.30 * c + 0.20 * s, 2)

    def get_reasoning(self, scores: dict[str, int]) -> str:
        return (
            f"Demonstrated commanding leadership ({scores.get('Leadership', 0)}/100) "
            f"and active squad communication ({scores.get('Communication', 0)}/100), "
            "taking natural ownership of shotcalling and lobby draft cohesion."
        )


class SupportRule(BaseRoleRule):
    """Support: High Teamwork, Communication, and disciplined selflessness."""

    def __init__(self) -> None:
        super().__init__(
            name="Support",
            description="Empowers teammates through economy sharing, peeling, utility assistance, and active encouragement.",
        )

    def calculate_affinity(self, scores: dict[str, int]) -> float:
        t = scores.get("Teamwork", 0)
        c = scores.get("Communication", 0)
        a = scores.get("Aggression", 0)
        # Supports excel in teamwork, communication, and measured patience
        return round(0.50 * t + 0.30 * c + 0.20 * max(0, 100 - a), 2)

    def get_reasoning(self, scores: dict[str, int]) -> str:
        return (
            f"High teamwork score ({scores.get('Teamwork', 0)}/100) and communication ({scores.get('Communication', 0)}/100), "
            "prioritizing squad economy and teammate protection over solo stats."
        )


class StrategistRule(BaseRoleRule):
    """Strategist: Deep preparation, anti-meta planning, and pattern recognition."""

    def __init__(self) -> None:
        super().__init__(
            name="Strategist",
            description="Analyzes opponent tendencies, crafts counter-utility setups, and coordinates macro map control.",
        )

    def calculate_affinity(self, scores: dict[str, int]) -> float:
        s = scores.get("Strategy", 0)
        l = scores.get("Leadership", 0)
        c = scores.get("Communication", 0)
        return round(0.50 * s + 0.25 * l + 0.25 * c, 2)

    def get_reasoning(self, scores: dict[str, int]) -> str:
        return (
            f"Exceptional strategic foresight ({scores.get('Strategy', 0)}/100), "
            "adapting anti-flank traps and formulating structured counter-play against opponent patterns."
        )


class DuelistRule(BaseRoleRule):
    """Duelist: High Aggression, forward momentum, and decisive entry play."""

    def __init__(self) -> None:
        super().__init__(
            name="Duelist",
            description="Spearheads engagements with relentless forward aggression, hunting opening eliminations.",
        )

    def calculate_affinity(self, scores: dict[str, int]) -> float:
        a = scores.get("Aggression", 0)
        l = scores.get("Leadership", 0)
        s = scores.get("Strategy", 0)
        return round(0.60 * a + 0.25 * l + 0.15 * s, 2)

    def get_reasoning(self, scores: dict[str, int]) -> str:
        return (
            f"High aggression score ({scores.get('Aggression', 0)}/100), "
            "consistently seeking early space control, decisive duels, and forward momentum."
        )


class SentinelRule(BaseRoleRule):
    """Sentinel: Defense anchor, perimeter security, and controlled aggression."""

    def __init__(self) -> None:
        super().__init__(
            name="Sentinel",
            description="Locks down map territory, protects against flanks, and maintains ironclad defensive containment.",
        )

    def calculate_affinity(self, scores: dict[str, int]) -> float:
        s = scores.get("Strategy", 0)
        t = scores.get("Teamwork", 0)
        a = scores.get("Aggression", 0)
        return round(0.40 * s + 0.35 * t + 0.25 * max(0, 100 - a), 2)

    def get_reasoning(self, scores: dict[str, int]) -> str:
        return (
            f"Disciplined strategic positioning ({scores.get('Strategy', 0)}/100) and teamwork ({scores.get('Teamwork', 0)}/100), "
            "anchoring choke points and denying enemy flank opportunities."
        )


class ControllerRule(BaseRoleRule):
    """Controller: Vision denial, smoke utility, and battlefield orchestration."""

    def __init__(self) -> None:
        super().__init__(
            name="Controller",
            description="Controls battlefield geometry, slices territory with utility, and guides squad rotations.",
        )

    def calculate_affinity(self, scores: dict[str, int]) -> float:
        s = scores.get("Strategy", 0)
        t = scores.get("Teamwork", 0)
        c = scores.get("Communication", 0)
        return round(0.40 * s + 0.40 * t + 0.20 * c, 2)

    def get_reasoning(self, scores: dict[str, int]) -> str:
        return (
            f"Balanced strategic vision ({scores.get('Strategy', 0)}/100) and teamwork synergy ({scores.get('Teamwork', 0)}/100), "
            "orchestrating team sightlines and crossfire positioning."
        )


class RoleClassifierEngine:
    """
    Main rule-based evaluation engine.
    Applies registered rules to compute role affinities and select primary & secondary roles.
    """

    def __init__(self) -> None:
        self.rules: list[BaseRoleRule] = [
            LeaderRule(),
            SupportRule(),
            StrategistRule(),
            DuelistRule(),
            SentinelRule(),
            ControllerRule(),
        ]

    def calculate_category_scores(self, responses: Sequence[SurveyResponse]) -> dict[str, int]:
        """Calculates 0-100 scores for the 5 categories from survey responses."""
        grouped: dict[str, list[int]] = defaultdict(list)
        for resp in responses:
            if resp.category and resp.score is not None:
                grouped[resp.category].append(resp.score)

        categories = ["Leadership", "Communication", "Strategy", "Teamwork", "Aggression", "Confidence"]
        scores: dict[str, int] = {}
        for cat in categories:
            vals = grouped.get(cat, [])
            scores[cat] = round(sum(vals) / len(vals)) if vals else 50
        return scores

    def classify(self, responses: Sequence[SurveyResponse]) -> ClassificationResult:
        """
        Executes rule evaluation on responses and returns the complete classification result.
        """
        scores = self.calculate_category_scores(responses)

        # Calculate affinities for all rules
        affinities: dict[str, float] = {}
        rule_map: dict[str, BaseRoleRule] = {}

        for rule in self.rules:
            aff = rule.calculate_affinity(scores)
            affinities[rule.name] = aff
            rule_map[rule.name] = rule

        # Sort roles by affinity score descending
        sorted_roles = sorted(affinities.items(), key=lambda item: item[1], reverse=True)

        primary_name, primary_score = sorted_roles[0]
        secondary_name, secondary_score = sorted_roles[1] if len(sorted_roles) > 1 else (sorted_roles[0][0], sorted_roles[0][1])

        # Synthesize personality archetype from combination
        personality = self._derive_personality(primary_name, secondary_name)

        # Generate comprehensive reasoning
        primary_rule = rule_map[primary_name]
        secondary_rule = rule_map[secondary_name]

        reasoning = (
            f"Primary: {primary_name} ({primary_score}% affinity) - {primary_rule.get_reasoning(scores)} "
            f"Secondary: {secondary_name} ({secondary_score}% affinity) - {secondary_rule.get_reasoning(scores)}"
        )

        return ClassificationResult(
            primary_role=primary_name,
            secondary_role=secondary_name,
            personality=personality,
            scores=scores,
            role_affinities=affinities,
            reasoning=reasoning,
        )

    def _derive_personality(self, primary: str, secondary: str) -> str:
        """Maps role combinations to gamer personality archetypes."""
        archetype_matrix: dict[tuple[str, str], str] = {
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
            ("Controller", "Teamwork"): "The Crossfire Anchor",
        }
        return archetype_matrix.get((primary, secondary), f"The {primary}-{secondary} Hybrid")


# Singleton engine instance
classifier_engine = RoleClassifierEngine()
