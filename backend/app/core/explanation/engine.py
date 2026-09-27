"""
Core AI Explanation Engine using Template-Based Natural Language Generation (NLG).
Ingests Compatibility Results, Gamer DNA, tactical Roles, and Official Statistics
to formulate clear, human-readable explanations of player compatibility.
"""

from dataclasses import dataclass, field
import math
from typing import Any, Sequence

from app.core.compatibility.models import CompatibilityReport
from app.core.explanation.config import ExplanationConfig, default_explanation_config
from app.core.explanation.templates import (
    IMPROVEMENT_TEMPLATES,
    MATCH_TEMPLATES,
    MISMATCH_TEMPLATES,
    STRENGTHS_TEMPLATES,
    WEAKNESSES_TEMPLATES,
)


@dataclass
class PlayerExplanationContext:
    """Consolidated input contextualizing a player for explanation generation."""
    username: str = "Player"
    # Psychometrics (Gamer DNA)
    leadership: float = 50.0
    communication: float = 50.0
    aggression: float = 50.0
    strategy: float = 50.0
    teamwork: float = 50.0
    confidence: float = 50.0
    # Roles
    primary_role: str = "Support"
    secondary_role: str | None = None
    preferred_roles: list[str] = field(default_factory=list)
    # Competitive Telemetry
    rank: str = "Gold 1"
    rank_rating: int = 1000
    win_rate: float = 50.0
    matches_played: int = 20
    kd_ratio: float = 1.0
    # Logistics
    region: str = "NA-East"
    languages: list[str] = field(default_factory=lambda: ["en"])
    schedule_slots: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ExplanationResult:
    """Consolidated natural language explanation output."""
    headline: str
    compatibility_score: float
    tier: str
    match_reasons: list[str]
    mismatch_reasons: list[str]
    strengths_narrative: list[str]
    weaknesses_narrative: list[str]
    improvement_suggestions: list[str]
    confidence_score: float


class AIExplanationEngine:
    """
    Template-based NLG engine translating multi-dimensional synergy vectors,
    Gamer DNA traits, tactical roles, and competitive telemetry into actionable narratives.
    """

    def __init__(self, config: ExplanationConfig | None = None) -> None:
        self.config = config or default_explanation_config

    def generate_explanation(
        self,
        player_a: PlayerExplanationContext,
        player_b: PlayerExplanationContext,
        compatibility_report: CompatibilityReport | None = None,
    ) -> ExplanationResult:
        """
        Synthesizes human-readable explanation from player contexts and optional compatibility report.
        """
        # Determine base compatibility score & tier
        if compatibility_report:
            compat_score = round(compatibility_report.compatibility_score, 1)
            tier = compatibility_report.tier
            dim_scores = compatibility_report.dimension_scores
        else:
            compat_score, tier, dim_scores = self._estimate_baseline_compatibility(player_a, player_b)

        # 1. Why two players match
        match_reasons = self._generate_match_reasons(player_a, player_b, dim_scores)

        # 2. Why they don't match
        mismatch_reasons = self._generate_mismatch_reasons(player_a, player_b, dim_scores)

        # 3. Strengths narrative
        strengths = self._generate_strengths(player_a, player_b, dim_scores)

        # 4. Weaknesses narrative
        weaknesses = self._generate_weaknesses(player_a, player_b, dim_scores)

        # 5. Improvement & coaching suggestions
        suggestions = self._generate_improvement_suggestions(player_a, player_b, dim_scores)

        # 6. Headline synthesis
        headline = self._synthesize_headline(player_a, player_b, compat_score, tier)

        # 7. Algorithmic confidence score
        confidence = self._calculate_confidence(player_a, player_b)

        return ExplanationResult(
            headline=headline,
            compatibility_score=compat_score,
            tier=tier,
            match_reasons=match_reasons[: self.config.max_match_reasons],
            mismatch_reasons=mismatch_reasons[: self.config.max_mismatch_reasons],
            strengths_narrative=strengths[: self.config.max_strengths],
            weaknesses_narrative=weaknesses[: self.config.max_weaknesses],
            improvement_suggestions=suggestions[: self.config.max_suggestions],
            confidence_score=confidence,
        )

    # --------------------------------------------------------------------------
    # Sub-generators
    # --------------------------------------------------------------------------

    def _generate_match_reasons(
        self,
        p_a: PlayerExplanationContext,
        p_b: PlayerExplanationContext,
        dims: dict[str, float],
    ) -> list[str]:
        """Formulates key reasons explaining positive synergy between the two players."""
        reasons: list[str] = []

        # 1. Leadership Dynamic
        lead_a, lead_b = p_a.leadership, p_b.leadership
        if (lead_a >= self.config.clash_leadership_threshold and lead_b <= self.config.supportive_leadership_threshold) or (
            lead_b >= self.config.clash_leadership_threshold and lead_a <= self.config.supportive_leadership_threshold
        ):
            leader = p_a.username if lead_a > lead_b else p_b.username
            lead_score = max(lead_a, lead_b)
            follower = p_b.username if lead_a > lead_b else p_a.username
            foll_score = min(lead_a, lead_b)
            tmpl = MATCH_TEMPLATES["leadership_complementary"][0]
            reasons.append(tmpl.format(leader=leader, lead_score=lead_score, follower=follower, foll_score=foll_score))

        # 2. Communication Alignment
        if min(p_a.communication, p_b.communication) >= self.config.high_comms_threshold or dims.get("communication", 0) >= 80:
            tmpl = MATCH_TEMPLATES["communication_alignment"][0]
            reasons.append(tmpl.format(player_a=p_a.username, comms_a=p_a.communication, player_b=p_b.username, comms_b=p_b.communication))

        # 3. Aggression / Pacing Harmony
        delta_aggr = abs(p_a.aggression - p_b.aggression)
        if 20.0 <= delta_aggr <= 45.0 or (max(p_a.aggression, p_b.aggression) >= 75 and min(p_a.aggression, p_b.aggression) >= 50):
            aggr_player = p_a.username if p_a.aggression > p_b.aggression else p_b.username
            aggr_score = max(p_a.aggression, p_b.aggression)
            supp_player = p_b.username if p_a.aggression > p_b.aggression else p_a.username
            supp_score = min(p_a.aggression, p_b.aggression)
            tmpl = MATCH_TEMPLATES["aggression_harmony"][0]
            reasons.append(tmpl.format(aggr_player=aggr_player, aggr_score=aggr_score, support_player=supp_player, supp_score=supp_score))

        # 4. Tactical Role Synergy
        role_a, role_b = p_a.primary_role, p_b.primary_role
        if role_a.lower() != role_b.lower() or dims.get("preferred_role", 0) >= 75:
            tmpl = MATCH_TEMPLATES["role_synergy"][0]
            reasons.append(tmpl.format(player_a=p_a.username, role_a=role_a, player_b=p_b.username, role_b=role_b))

        # 5. Skill & Rank Parity
        mmr_delta = abs(p_a.rank_rating - p_b.rank_rating)
        if mmr_delta <= 250 or dims.get("official_rank", 0) >= 75:
            tmpl = MATCH_TEMPLATES["skill_parity"][0]
            reasons.append(tmpl.format(mmr_delta=mmr_delta, rank_a=p_a.rank, rank_b=p_b.rank))

        # 6. Regional & Logistics
        shared_langs = set(p_a.languages).intersection(set(p_b.languages))
        if p_a.region.lower() == p_b.region.lower() and shared_langs:
            tmpl = MATCH_TEMPLATES["logistics_alignment"][0]
            reasons.append(tmpl.format(region=p_a.region))

        if not reasons:
            reasons.append(f"Basic cooperative baseline: {p_a.username} and {p_b.username} share compatible team objectives.")

        return reasons

    def _generate_mismatch_reasons(
        self,
        p_a: PlayerExplanationContext,
        p_b: PlayerExplanationContext,
        dims: dict[str, float],
    ) -> list[str]:
        """Formulates key reasons explaining potential friction or negative alignment."""
        reasons: list[str] = []

        # 1. Dual-leadership Clash
        if p_a.leadership >= self.config.clash_leadership_threshold and p_b.leadership >= self.config.clash_leadership_threshold:
            tmpl = MISMATCH_TEMPLATES["dual_leadership_clash"][0]
            reasons.append(tmpl.format(player_a=p_a.username, lead_a=p_a.leadership, player_b=p_b.username, lead_b=p_b.leadership))

        # 2. Rudderless (Both low leadership)
        elif max(p_a.leadership, p_b.leadership) < 50.0:
            tmpl = MISMATCH_TEMPLATES["rudderless_squad"][0]
            reasons.append(tmpl.format(max_lead=max(p_a.leadership, p_b.leadership)))

        # 3. Communication Deficit
        if min(p_a.communication, p_b.communication) < self.config.silent_comms_threshold or dims.get("communication", 100) < 50:
            tmpl = MISMATCH_TEMPLATES["communication_deficit"][0]
            reasons.append(tmpl.format(comms_a=p_a.communication, comms_b=p_b.communication))

        # 4. Aggression Disconnect
        delta_aggr = abs(p_a.aggression - p_b.aggression)
        if delta_aggr >= self.config.aggression_delta_threshold:
            aggr_p = p_a.username if p_a.aggression > p_b.aggression else p_b.username
            pass_p = p_b.username if p_a.aggression > p_b.aggression else p_a.username
            tmpl = MISMATCH_TEMPLATES["aggression_disconnect"][0]
            reasons.append(tmpl.format(delta_aggr=delta_aggr, aggr_player=aggr_p, passive_player=pass_p))

        # 5. Role Collision
        if p_a.primary_role.lower() == p_b.primary_role.lower():
            tmpl = MISMATCH_TEMPLATES["role_collision"][0]
            reasons.append(tmpl.format(player_a=p_a.username, player_b=p_b.username, role=p_a.primary_role))

        # 6. Skill Disparity
        mmr_delta = abs(p_a.rank_rating - p_b.rank_rating)
        if mmr_delta >= self.config.rank_disparity_mmr or dims.get("official_rank", 100) < 50:
            tmpl = MISMATCH_TEMPLATES["skill_disparity"][0]
            reasons.append(tmpl.format(mmr_delta=mmr_delta, rank_a=p_a.rank, rank_b=p_b.rank))

        # 7. Logistics / Regional mismatch
        if p_a.region.lower() != p_b.region.lower():
            tmpl = MISMATCH_TEMPLATES["logistics_mismatch"][0]
            reasons.append(tmpl.format(reg_a=p_a.region, reg_b=p_b.region))

        # 8. Language barrier
        shared_langs = set(p_a.languages).intersection(set(p_b.languages))
        if not shared_langs:
            tmpl = MISMATCH_TEMPLATES["language_barrier"][0]
            reasons.append(tmpl)

        if not reasons:
            reasons.append("No critical friction points detected; general tactical execution remains smooth.")

        return reasons

    def _generate_strengths(
        self,
        p_a: PlayerExplanationContext,
        p_b: PlayerExplanationContext,
        dims: dict[str, float],
    ) -> list[str]:
        """Selects narrative descriptions for standout duo strengths."""
        strengths: list[str] = []

        # Role Diversity
        if p_a.primary_role.lower() != p_b.primary_role.lower():
            strengths.append(STRENGTHS_TEMPLATES["role_diversity"].format(role_a=p_a.primary_role, role_b=p_b.primary_role))

        # Verbal Coordination
        if min(p_a.communication, p_b.communication) >= 70.0 or dims.get("communication", 0) >= 75:
            strengths.append(STRENGTHS_TEMPLATES["verbal_coordination"])

        # Command Clarity
        if abs(p_a.leadership - p_b.leadership) >= 20.0 and max(p_a.leadership, p_b.leadership) >= 70.0:
            leader = p_a.username if p_a.leadership > p_b.leadership else p_b.username
            follower = p_b.username if p_a.leadership > p_b.leadership else p_a.username
            strengths.append(STRENGTHS_TEMPLATES["command_clarity"].format(leader=leader, follower=follower))

        # Frontline / Anchor dynamic
        if max(p_a.aggression, p_b.aggression) >= 75.0 and min(p_a.aggression, p_b.aggression) >= 45.0:
            strengths.append(STRENGTHS_TEMPLATES["frontline_anchor_dynamic"])

        # Lobby Parity
        if abs(p_a.rank_rating - p_b.rank_rating) <= 200:
            strengths.append(STRENGTHS_TEMPLATES["lobby_parity"])

        # Schedule Overlap
        if dims.get("schedule", 0) >= 80.0 or (p_a.schedule_slots and any(s in p_b.schedule_slots for s in p_a.schedule_slots)):
            strengths.append(STRENGTHS_TEMPLATES["shared_schedule"])

        if not strengths:
            strengths.append(f"Balanced foundation: {p_a.username} and {p_b.username} demonstrate solid competitive consistency.")

        return strengths

    def _generate_weaknesses(
        self,
        p_a: PlayerExplanationContext,
        p_b: PlayerExplanationContext,
        dims: dict[str, float],
    ) -> list[str]:
        """Selects narrative descriptions for duo vulnerabilities."""
        weaknesses: list[str] = []

        # Ego tension
        if p_a.leadership >= 75.0 and p_b.leadership >= 75.0:
            weaknesses.append(WEAKNESSES_TEMPLATES["ego_tension"])

        # Silent collapse
        if min(p_a.communication, p_b.communication) < 50.0:
            weaknesses.append(WEAKNESSES_TEMPLATES["silent_collapse"])

        # Trade lag
        if abs(p_a.aggression - p_b.aggression) >= 30.0:
            weaknesses.append(WEAKNESSES_TEMPLATES["trade_lag"])

        # Role pool overlap
        if p_a.primary_role.lower() == p_b.primary_role.lower():
            weaknesses.append(WEAKNESSES_TEMPLATES["pool_overlap"].format(role=p_a.primary_role))

        # Rank tilt / Win rate gap
        if abs(p_a.win_rate - p_b.win_rate) >= self.config.win_rate_gap_threshold or abs(p_a.rank_rating - p_b.rank_rating) >= 350:
            weaknesses.append(WEAKNESSES_TEMPLATES["rank_tilt"].format(wr_a=p_a.win_rate, wr_b=p_b.win_rate))

        # Schedule fragmentation
        if dims.get("schedule", 100) < 50.0:
            weaknesses.append(WEAKNESSES_TEMPLATES["schedule_fragmentation"])

        if not weaknesses:
            weaknesses.append("Minimal structural weaknesses; primary focus should be on maintaining in-game vocal consistency.")

        return weaknesses

    def _generate_improvement_suggestions(
        self,
        p_a: PlayerExplanationContext,
        p_b: PlayerExplanationContext,
        dims: dict[str, float],
    ) -> list[str]:
        """Generates concrete tactical and communication coaching advice."""
        suggestions: list[str] = []

        # Shotcaller protocol
        if (p_a.leadership >= 70.0 and p_b.leadership >= 70.0) or (p_a.leadership < 50.0 and p_b.leadership < 50.0):
            suggestions.append(IMPROVEMENT_TEMPLATES["shotcaller_protocol"])

        # Communication cadence
        if min(p_a.communication, p_b.communication) < 70.0 or dims.get("communication", 100) < 70:
            suggestions.append(IMPROVEMENT_TEMPLATES["comms_cadence"])

        # Role flexing
        if p_a.primary_role.lower() == p_b.primary_role.lower():
            p_user = p_a.username if len(p_a.preferred_roles) > 1 else p_b.username
            s_user = p_b.username if p_user == p_a.username else p_a.username
            suggestions.append(IMPROVEMENT_TEMPLATES["role_flexing"].format(primary_user=p_user, secondary_user=s_user))

        # Buddy spacing & trades
        if abs(p_a.aggression - p_b.aggression) >= 25.0:
            suggestions.append(IMPROVEMENT_TEMPLATES["buddy_spacing"])

        # Crosshair trade drills
        if abs(p_a.rank_rating - p_b.rank_rating) >= 200:
            suggestions.append(IMPROVEMENT_TEMPLATES["crosshair_trade_drills"])

        # Schedule anchor
        if dims.get("schedule", 100) < 65:
            suggestions.append(IMPROVEMENT_TEMPLATES["schedule_anchor"])

        if not suggestions:
            suggestions.append("Continue executing structured default rounds and refining post-plant crossfire setups.")

        return suggestions

    # --------------------------------------------------------------------------
    # Helper & Synthesis
    # --------------------------------------------------------------------------

    def _synthesize_headline(
        self,
        p_a: PlayerExplanationContext,
        p_b: PlayerExplanationContext,
        score: float,
        tier: str,
    ) -> str:
        """Formulates an executive summary headline characterizing the duo."""
        role_a = p_a.primary_role
        role_b = p_b.primary_role

        if score >= 90.0:
            return f"Optimal Tactical Synergy: Elite {role_a} and {role_b} Co-op Dynamic ({tier})"
        elif score >= 75.0:
            return f"Strong Tactical Alignment: High-Chemistry {role_a} & {role_b} Duo ({tier})"
        elif score >= 60.0:
            return f"Moderate Chemistry: Functional {role_a}-{role_b} Pairing with Adaptation Potential ({tier})"
        elif score >= 45.0:
            return f"Questionable Synergy: High Disconnect Risk Between {role_a} and {role_b} ({tier})"
        else:
            return f"Severe Friction Warning: Counter-Productive {role_a} & {role_b} Pairing ({tier})"

    def _estimate_baseline_compatibility(
        self,
        p_a: PlayerExplanationContext,
        p_b: PlayerExplanationContext,
    ) -> tuple[float, str, dict[str, float]]:
        """Estimates baseline compatibility when an external report is not passed."""
        # Dimension scores
        lead_s = 95.0 if abs(p_a.leadership - p_b.leadership) >= 20 else (45.0 if p_a.leadership >= 75 and p_b.leadership >= 75 else 75.0)
        comm_s = min(100.0, (p_a.communication + p_b.communication) / 2.0)
        aggr_s = max(40.0, 100.0 - abs(p_a.aggression - p_b.aggression))
        strat_s = max(50.0, 100.0 - abs(p_a.strategy - p_b.strategy))
        role_s = 95.0 if p_a.primary_role.lower() != p_b.primary_role.lower() else 35.0
        mmr_s = max(30.0, 100.0 - (abs(p_a.rank_rating - p_b.rank_rating) / 10.0))
        reg_s = 100.0 if p_a.region.lower() == p_b.region.lower() else 30.0
        lang_s = 100.0 if set(p_a.languages).intersection(set(p_b.languages)) else 0.0

        score = round(
            0.15 * lead_s
            + 0.15 * comm_s
            + 0.10 * aggr_s
            + 0.10 * strat_s
            + 0.15 * role_s
            + 0.15 * mmr_s
            + 0.10 * reg_s
            + 0.10 * lang_s,
            1,
        )

        if score >= 90.0:
            tier = "Optimal Duo Synergy"
        elif score >= 75.0:
            tier = "Strong Compatibility"
        elif score >= 60.0:
            tier = "Moderate Synergy"
        elif score >= 45.0:
            tier = "Questionable Alignment"
        else:
            tier = "High Friction Risk"

        dims = {
            "leadership": lead_s,
            "communication": comm_s,
            "aggression": aggr_s,
            "strategy": strat_s,
            "preferred_role": role_s,
            "official_rank": mmr_s,
            "region": reg_s,
            "language": lang_s,
        }
        return score, tier, dims

    def _calculate_confidence(
        self,
        p_a: PlayerExplanationContext,
        p_b: PlayerExplanationContext,
    ) -> float:
        """Calculates algorithmic explanation confidence score based on input completeness."""
        conf = 0.50
        if p_a.matches_played >= 10 and p_b.matches_played >= 10:
            conf += 0.20
        if p_a.rank and p_b.rank and p_a.rank != "Unranked" and p_b.rank != "Unranked":
            conf += 0.15
        if p_a.preferred_roles and p_b.preferred_roles:
            conf += 0.10
        if p_a.schedule_slots and p_b.schedule_slots:
            conf += 0.05
        return round(min(1.0, conf), 2)


default_explanation_engine = AIExplanationEngine()
