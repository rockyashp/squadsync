"""
Rule implementations for the Gamer Role Classification Engine.
Evaluates multi-signal evidence across Gamer DNA, official game statistics,
player preferences, and game context for each tactical archetype:
- Leader
- Support
- Strategist
- Duelist
- Sentinel
- Controller
"""

from app.core.role_classifier.base import BaseRoleRule, RuleEvaluation
from app.core.role_classifier.config import RoleClassificationConfig
from app.core.role_classifier.features import GamerRoleFeatures


class LeaderRule(BaseRoleRule):
    """
    Leader / In-Game Leader (IGL) Rule:
    - High psychometric Leadership, Communication, and Confidence.
    - Official telemetry showing above-average win rate (shotcalling effectiveness)
      and solid cross-round consistency.
    - Stated preference for IGL/Captain.
    """

    def __init__(self) -> None:
        super().__init__(
            name="Leader",
            description="Commands round tempo, inspires squad confidence, and shotcalls during high-pressure rounds.",
        )

    def evaluate(
        self,
        features: GamerRoleFeatures,
        config: RoleClassificationConfig,
    ) -> RuleEvaluation:
        dna = features.dna
        stats = features.stats

        # 1. DNA Score: 45% Leadership + 35% Communication + 20% Confidence
        dna_score = round(
            0.45 * dna.leadership + 0.35 * dna.communication + 0.20 * dna.confidence,
            2,
        )

        # 2. Stats Score: Shotcalling value is strongly reflected in Win Rate
        stats_norm = stats.normalize(config.benchmarks)
        # Win rate (50%) + consistent KD (30%) + match experience (20%)
        stat_score = round(
            (0.50 * stats_norm["win_rate_norm"] + 0.30 * stats_norm["kd_norm"] + 0.20 * stats_norm["sample_factor"]) * 100.0,
            2,
        )

        # 3. Preference Score
        pref_score = self.calculate_preference_score(features.preferred_roles, config)

        # 4. Game Context Score
        game_score = self.calculate_game_context_score(
            features.preferred_games, stats.favorite_heroes_or_agents, config
        )

        # Composite affinity using configured signal weights
        w = config.weights
        affinity = round(
            w.dna_weight * dna_score
            + w.stats_weight * stat_score
            + w.preferred_roles_weight * pref_score
            + w.preferred_games_weight * game_score,
            2,
        )

        reasoning = (
            f"Commanding leadership ({dna.leadership:.0f}/100) and assertive squad communication "
            f"({dna.communication:.0f}/100), corroborated by a {stats.win_rate:.1f}% competitive win rate "
            f"demonstrating decisive match tempo direction."
        )

        return RuleEvaluation(
            role_name=self.name,
            affinity_score=affinity,
            dna_score=dna_score,
            stats_score=stat_score,
            preference_score=pref_score,
            game_score=game_score,
            reasoning_snippet=reasoning,
        )


class SupportRule(BaseRoleRule):
    """
    Support Rule:
    - High psychometric Teamwork and Communication, balanced with measured patience.
    - Official telemetry showing high KDA (assist impact) even with moderate solo KD.
    - Stated preference for Support / Enabler.
    """

    def __init__(self) -> None:
        super().__init__(
            name="Support",
            description="Empowers teammates through economy sharing, peeling, utility assistance, and active encouragement.",
        )

    def evaluate(
        self,
        features: GamerRoleFeatures,
        config: RoleClassificationConfig,
    ) -> RuleEvaluation:
        dna = features.dna
        stats = features.stats

        # 1. DNA Score: 50% Teamwork + 30% Communication + 20% controlled aggression
        dna_score = round(
            0.50 * dna.teamwork + 0.30 * dna.communication + 0.20 * max(0.0, 100.0 - dna.aggression),
            2,
        )

        # 2. Stats Score: High KDA (assists) + Win Rate
        stats_norm = stats.normalize(config.benchmarks)
        stat_score = round(
            (0.60 * stats_norm["kda_norm"] + 0.25 * stats_norm["win_rate_norm"] + 0.15 * stats_norm["sample_factor"]) * 100.0,
            2,
        )

        # 3. Preference Score
        pref_score = self.calculate_preference_score(features.preferred_roles, config)

        # 4. Game Context Score
        game_score = self.calculate_game_context_score(
            features.preferred_games, stats.favorite_heroes_or_agents, config
        )

        w = config.weights
        affinity = round(
            w.dna_weight * dna_score
            + w.stats_weight * stat_score
            + w.preferred_roles_weight * pref_score
            + w.preferred_games_weight * game_score,
            2,
        )

        reasoning = (
            f"Selfless teamwork orientation ({dna.teamwork:.0f}/100) and high assist conversion "
            f"(KDA {stats.kda:.2f}), prioritizing team survival and utility peeling over solo stat accumulation."
        )

        return RuleEvaluation(
            role_name=self.name,
            affinity_score=affinity,
            dna_score=dna_score,
            stats_score=stat_score,
            preference_score=pref_score,
            game_score=game_score,
            reasoning_snippet=reasoning,
        )


class StrategistRule(BaseRoleRule):
    """
    Strategist Rule:
    - High psychometric Strategy and Leadership, with analytical foresight.
    - Telemetry indicating consistent round conversion and disciplined tactical play.
    - Stated preference for Tactician/Strategist.
    """

    def __init__(self) -> None:
        super().__init__(
            name="Strategist",
            description="Analyzes opponent tendencies, crafts counter-utility setups, and coordinates macro map control.",
        )

    def evaluate(
        self,
        features: GamerRoleFeatures,
        config: RoleClassificationConfig,
    ) -> RuleEvaluation:
        dna = features.dna
        stats = features.stats

        # 1. DNA Score: 55% Strategy + 25% Leadership + 20% Communication
        dna_score = round(
            0.55 * dna.strategy + 0.25 * dna.leadership + 0.20 * dna.communication,
            2,
        )

        # 2. Stats Score: High win rate + solid KDA stability
        stats_norm = stats.normalize(config.benchmarks)
        stat_score = round(
            (0.50 * stats_norm["win_rate_norm"] + 0.30 * stats_norm["kda_norm"] + 0.20 * stats_norm["kd_norm"]) * 100.0,
            2,
        )

        pref_score = self.calculate_preference_score(features.preferred_roles, config)
        game_score = self.calculate_game_context_score(
            features.preferred_games, stats.favorite_heroes_or_agents, config
        )

        w = config.weights
        affinity = round(
            w.dna_weight * dna_score
            + w.stats_weight * stat_score
            + w.preferred_roles_weight * pref_score
            + w.preferred_games_weight * game_score,
            2,
        )

        reasoning = (
            f"Exceptional strategic foresight ({dna.strategy:.0f}/100) and structured game planning, "
            f"complemented by sustained win rate consistency ({stats.win_rate:.1f}%) through macro rotations."
        )

        return RuleEvaluation(
            role_name=self.name,
            affinity_score=affinity,
            dna_score=dna_score,
            stats_score=stat_score,
            preference_score=pref_score,
            game_score=game_score,
            reasoning_snippet=reasoning,
        )


class DuelistRule(BaseRoleRule):
    """
    Duelist Rule:
    - High psychometric Aggression and Confidence.
    - High KD ratio, high headshot %, high damage/score per round.
    - Stated preference for Entry / Carry / Duelist.
    """

    def __init__(self) -> None:
        super().__init__(
            name="Duelist",
            description="Spearheads engagements with relentless forward aggression, hunting opening eliminations.",
        )

    def evaluate(
        self,
        features: GamerRoleFeatures,
        config: RoleClassificationConfig,
    ) -> RuleEvaluation:
        dna = features.dna
        stats = features.stats

        # 1. DNA Score: 55% Aggression + 30% Confidence + 15% Leadership
        dna_score = round(
            0.55 * dna.aggression + 0.30 * dna.confidence + 0.15 * dna.leadership,
            2,
        )

        # 2. Stats Score: Heavy emphasis on KD ratio (50%), Headshot % (30%), Win rate (20%)
        stats_norm = stats.normalize(config.benchmarks)
        stat_score = round(
            (0.50 * stats_norm["kd_norm"] + 0.30 * stats_norm["headshot_norm"] + 0.20 * stats_norm["win_rate_norm"]) * 100.0,
            2,
        )

        pref_score = self.calculate_preference_score(features.preferred_roles, config)
        game_score = self.calculate_game_context_score(
            features.preferred_games, stats.favorite_heroes_or_agents, config
        )

        w = config.weights
        affinity = round(
            w.dna_weight * dna_score
            + w.stats_weight * stat_score
            + w.preferred_roles_weight * pref_score
            + w.preferred_games_weight * game_score,
            2,
        )

        hs_str = f" and {stats.headshot_pct:.1f}% headshot accuracy" if stats.headshot_pct is not None else ""
        reasoning = (
            f"Relentless forward momentum ({dna.aggression:.0f}/100 aggression, {dna.confidence:.0f}/100 confidence), "
            f"substantiated by strong lethal output ({stats.kd_ratio:.2f} K/D{hs_str}) to secure opening duel space."
        )

        return RuleEvaluation(
            role_name=self.name,
            affinity_score=affinity,
            dna_score=dna_score,
            stats_score=stat_score,
            preference_score=pref_score,
            game_score=game_score,
            reasoning_snippet=reasoning,
        )


class SentinelRule(BaseRoleRule):
    """
    Sentinel Rule:
    - High psychometric Strategy and Teamwork with disciplined patience.
    - Telemetry indicating reliable KD ratio, lower death counts, and strong defensive anchor presence.
    - Stated preference for Sentinel / Site Anchor.
    """

    def __init__(self) -> None:
        super().__init__(
            name="Sentinel",
            description="Locks down map territory, protects against flanks, and maintains ironclad defensive containment.",
        )

    def evaluate(
        self,
        features: GamerRoleFeatures,
        config: RoleClassificationConfig,
    ) -> RuleEvaluation:
        dna = features.dna
        stats = features.stats

        # 1. DNA Score: 45% Strategy + 35% Teamwork + 20% Patience (100 - Aggression)
        dna_score = round(
            0.45 * dna.strategy + 0.35 * dna.teamwork + 0.20 * max(0.0, 100.0 - dna.aggression),
            2,
        )

        # 2. Stats Score: KD consistency (40%) + KDA (35%) + Win Rate (25%)
        stats_norm = stats.normalize(config.benchmarks)
        stat_score = round(
            (0.40 * stats_norm["kd_norm"] + 0.35 * stats_norm["kda_norm"] + 0.25 * stats_norm["win_rate_norm"]) * 100.0,
            2,
        )

        pref_score = self.calculate_preference_score(features.preferred_roles, config)
        game_score = self.calculate_game_context_score(
            features.preferred_games, stats.favorite_heroes_or_agents, config
        )

        w = config.weights
        affinity = round(
            w.dna_weight * dna_score
            + w.stats_weight * stat_score
            + w.preferred_roles_weight * pref_score
            + w.preferred_games_weight * game_score,
            2,
        )

        reasoning = (
            f"Disciplined positioning and site lockdown focus ({dna.strategy:.0f}/100 strategy, {dna.teamwork:.0f}/100 teamwork), "
            f"demonstrating patient defensive containment with reliable survivability ({stats.kd_ratio:.2f} K/D)."
        )

        return RuleEvaluation(
            role_name=self.name,
            affinity_score=affinity,
            dna_score=dna_score,
            stats_score=stat_score,
            preference_score=pref_score,
            game_score=game_score,
            reasoning_snippet=reasoning,
        )


class ControllerRule(BaseRoleRule):
    """
    Controller Rule:
    - High psychometric Strategy, Teamwork, and Communication.
    - Telemetry showing high assist generation and round conversion via spatial utility.
    - Stated preference for Controller / Smoker.
    """

    def __init__(self) -> None:
        super().__init__(
            name="Controller",
            description="Controls battlefield geometry, slices territory with utility, and guides squad rotations.",
        )

    def evaluate(
        self,
        features: GamerRoleFeatures,
        config: RoleClassificationConfig,
    ) -> RuleEvaluation:
        dna = features.dna
        stats = features.stats

        # 1. DNA Score: 40% Strategy + 35% Teamwork + 25% Communication
        dna_score = round(
            0.40 * dna.strategy + 0.35 * dna.teamwork + 0.25 * dna.communication,
            2,
        )

        # 2. Stats Score: Assist conversion / KDA (50%) + Win rate (35%) + sample stability (15%)
        stats_norm = stats.normalize(config.benchmarks)
        stat_score = round(
            (0.50 * stats_norm["kda_norm"] + 0.35 * stats_norm["win_rate_norm"] + 0.15 * stats_norm["sample_factor"]) * 100.0,
            2,
        )

        pref_score = self.calculate_preference_score(features.preferred_roles, config)
        game_score = self.calculate_game_context_score(
            features.preferred_games, stats.favorite_heroes_or_agents, config
        )

        w = config.weights
        affinity = round(
            w.dna_weight * dna_score
            + w.stats_weight * stat_score
            + w.preferred_roles_weight * pref_score
            + w.preferred_games_weight * game_score,
            2,
        )

        reasoning = (
            f"Spatial orchestration and vision denial focus ({dna.strategy:.0f}/100 strategy, {dna.communication:.0f}/100 comms), "
            f"controlling key choke points and creating protected entry corridors (KDA {stats.kda:.2f})."
        )

        return RuleEvaluation(
            role_name=self.name,
            affinity_score=affinity,
            dna_score=dna_score,
            stats_score=stat_score,
            preference_score=pref_score,
            game_score=game_score,
            reasoning_snippet=reasoning,
        )
