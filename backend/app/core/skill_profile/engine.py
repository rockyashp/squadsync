"""
SkillProfileEngine orchestrator.
Coordinates the 6 skill evaluators, aggregates radar chart coordinates,
derives overall player rating, and highlights top strengths and growth areas.
"""

from dataclasses import dataclass, field
from typing import Sequence

from app.core.role_classifier.features import GamerDNAVector, OfficialGameStats
from app.core.skill_profile.config import (
    SkillProfileConfig,
    default_skill_config,
)
from app.core.skill_profile.evaluators import (
    BaseSkillEvaluator,
    CommunicationEvaluator,
    ConsistencyEvaluator,
    DecisionMakingEvaluator,
    GameSenseEvaluator,
    LeadershipEvaluator,
    MechanicalSkillEvaluator,
    SkillDimensionResult,
)


@dataclass(frozen=True)
class SkillProfileResult:
    """Consolidated result for the entire 6-dimensional skill profile."""
    overall_score: float
    overall_tier: str
    mechanical_skill: SkillDimensionResult
    communication: SkillDimensionResult
    leadership: SkillDimensionResult
    consistency: SkillDimensionResult
    decision_making: SkillDimensionResult
    game_sense: SkillDimensionResult
    radar_chart: dict[str, float]
    top_strengths: list[str]
    growth_areas: list[str]


class SkillProfileEngine:
    """
    Orchestrates competitive skill profile generation from Survey, DNA, and Official Stats.
    """

    def __init__(
        self,
        config: SkillProfileConfig | None = None,
        evaluators: Sequence[BaseSkillEvaluator] | None = None,
    ) -> None:
        self.config = config or default_skill_config
        self.evaluators: dict[str, BaseSkillEvaluator] = {
            "mechanical_skill": MechanicalSkillEvaluator(),
            "communication": CommunicationEvaluator(),
            "leadership": LeadershipEvaluator(),
            "consistency": ConsistencyEvaluator(),
            "decision_making": DecisionMakingEvaluator(),
            "game_sense": GameSenseEvaluator(),
        } if evaluators is None else {e.name.lower().replace(" ", "_"): e for e in evaluators}

    def generate(
        self,
        dna: GamerDNAVector,
        stats: OfficialGameStats,
    ) -> SkillProfileResult:
        """
        Executes evaluation for all 6 skill dimensions and synthesizes the full profile.
        """
        mechanical = self.evaluators["mechanical_skill"].evaluate(dna, stats, self.config)
        communication = self.evaluators["communication"].evaluate(dna, stats, self.config)
        leadership = self.evaluators["leadership"].evaluate(dna, stats, self.config)
        consistency = self.evaluators["consistency"].evaluate(dna, stats, self.config)
        decision_making = self.evaluators["decision_making"].evaluate(dna, stats, self.config)
        game_sense = self.evaluators["game_sense"].evaluate(dna, stats, self.config)

        dimensions = [mechanical, communication, leadership, consistency, decision_making, game_sense]

        # Overall composite rating
        overall_score = round(sum(d.score for d in dimensions) / len(dimensions), 1)
        overall_tier = self.config.get_tier(overall_score).value

        # Radar chart coordinates (0-100 values)
        radar_chart = {d.name: d.score for d in dimensions}

        # Identify strengths (top 2 scoring dimensions)
        sorted_by_score = sorted(dimensions, key=lambda d: d.score, reverse=True)
        top_strengths = [
            f"{d.name} ({d.score:.1f}/100 - {d.tier}): Strong competitive asset"
            for d in sorted_by_score[:2]
        ]

        # Identify growth areas (lowest 2 scoring dimensions)
        growth_areas = [
            f"{d.name} ({d.score:.1f}/100 - {d.tier}): Focus on targeted practice and training drills"
            for d in sorted_by_score[-2:]
        ]

        return SkillProfileResult(
            overall_score=overall_score,
            overall_tier=overall_tier,
            mechanical_skill=mechanical,
            communication=communication,
            leadership=leadership,
            consistency=consistency,
            decision_making=decision_making,
            game_sense=game_sense,
            radar_chart=radar_chart,
            top_strengths=top_strengths,
            growth_areas=growth_areas,
        )


default_skill_engine = SkillProfileEngine()
