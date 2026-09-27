"""
Evaluator implementations comparing Player A and Player B across the 10 dimensions:
1. Leadership
2. Communication
3. Aggression
4. Strategy
5. Region
6. Language
7. Schedule
8. Official Rank
9. Win Rate
10. Preferred Role
"""

from app.core.compatibility.config import AICompatibilityConfig, default_compatibility_config
from app.core.compatibility.models import DimensionScore, PlayerComparisonInput


class PsychometricEvaluator:
    """Evaluates behavioral and personality synergy from Gamer DNA."""

    def evaluate(
        self,
        player_a: PlayerComparisonInput,
        player_b: PlayerComparisonInput,
        config: AICompatibilityConfig,
    ) -> list[DimensionScore]:
        w = config.weights
        th = config.thresholds
        results: list[DimensionScore] = []

        # 1. Leadership Comparison (Complementary vs. Clash)
        l_a, l_b = player_a.leadership, player_b.leadership
        if l_a >= th.high_leadership_threshold and l_b >= th.high_leadership_threshold:
            l_score = 45.0
            l_assessment = "Dual dominant shotcallers; potential ego clash on mid-round calls."
        elif (l_a >= 70.0 and l_b <= 65.0) or (l_b >= 70.0 and l_a <= 65.0):
            l_score = 95.0
            l_assessment = "Ideal leader-follower dynamic; clear shotcalling authority with disciplined support."
        elif l_a < 45.0 and l_b < 45.0:
            l_score = 55.0
            l_assessment = "Both players lack vocal initiative; squad may suffer from passive hesitation."
        else:
            l_score = 80.0
            l_assessment = "Balanced leadership presence; collaborative tactical calls."

        results.append(
            DimensionScore(
                dimension="Leadership",
                score=round(l_score, 1),
                weight=w.leadership_weight,
                assessment=l_assessment,
            )
        )

        # 2. Communication Comparison
        c_a, c_b = player_a.communication, player_b.communication
        c_avg = (c_a + c_b) / 2.0
        c_diff = abs(c_a - c_b)
        c_score = max(20.0, min(100.0, c_avg - (c_diff * 0.25)))

        if c_a >= 75.0 and c_b >= 75.0:
            c_assessment = "Both players provide crisp, continuous vocal callouts and active utility tracking."
        elif c_a < 45.0 and c_b < 45.0:
            c_assessment = "Both players are low-volume communicators; high risk of silent round collapse."
        else:
            c_assessment = "Moderate communicative alignment; one player will need to guide voice callouts."

        results.append(
            DimensionScore(
                dimension="Communication",
                score=round(c_score, 1),
                weight=w.communication_weight,
                assessment=c_assessment,
            )
        )

        # 3. Aggression Comparison (Entry & Support Pacing)
        a_a, a_b = player_a.aggression, player_b.aggression
        if a_a >= 70.0 and a_b >= 70.0:
            aggr_score = 85.0
            aggr_assessment = "High-octane aggression; explosive synchronized entries but vulnerable to counter-utility."
        elif (a_a >= 70.0 and a_b <= 50.0) or (a_b >= 70.0 and a_a <= 50.0):
            aggr_score = 92.0
            aggr_assessment = "Complementary pacing; aggressive entry paired with patient anchor and trade support."
        elif a_a <= 40.0 and a_b <= 40.0:
            aggr_score = 60.0
            aggr_assessment = "Overly passive engagement style; team may forfeit space and round timer control."
        else:
            aggr_score = 80.0
            aggr_assessment = "Harmonious engagement pace with adaptable aggression thresholds."

        results.append(
            DimensionScore(
                dimension="Aggression",
                score=round(aggr_score, 1),
                weight=w.aggression_weight,
                assessment=aggr_assessment,
            )
        )

        # 4. Strategy Comparison (Macro Consensus)
        s_a, s_b = player_a.strategy, player_b.strategy
        s_diff = abs(s_a - s_b)
        strat_score = max(30.0, min(100.0, 100.0 - (s_diff * 0.75)))
        strat_assessment = (
            "Strong consensus on macro site hits, eco rounds, and rotation timing."
            if s_diff <= 15.0
            else "Divergent tactical philosophies; may disagree on when to commit or save."
        )

        results.append(
            DimensionScore(
                dimension="Strategy",
                score=round(strat_score, 1),
                weight=w.strategy_weight,
                assessment=strat_assessment,
            )
        )

        return results


class LogisticsEvaluator:
    """Evaluates regional ping, language overlap, and schedule alignment."""

    def evaluate(
        self,
        player_a: PlayerComparisonInput,
        player_b: PlayerComparisonInput,
        config: AICompatibilityConfig,
    ) -> list[DimensionScore]:
        w = config.weights
        results: list[DimensionScore] = []

        # 5. Region Comparison
        reg_a = player_a.region.strip().lower()
        reg_b = player_b.region.strip().lower()

        if reg_a == reg_b:
            reg_score = 100.0
            reg_assessment = f"Same server cluster ({player_a.region}); optimal low-latency connectivity."
        elif ("na" in reg_a and "na" in reg_b) or ("eu" in reg_a and "eu" in reg_b) or ("ap" in reg_a and "ap" in reg_b):
            reg_score = 75.0
            reg_assessment = f"Adjacent regional zones ({player_a.region} / {player_b.region}); minor ping difference."
        else:
            reg_score = 15.0
            reg_assessment = f"Cross-continental regions ({player_a.region} vs. {player_b.region}); severe latency penalty."

        results.append(
            DimensionScore(
                dimension="Region",
                score=round(reg_score, 1),
                weight=w.region_weight,
                assessment=reg_assessment,
            )
        )

        # 6. Language Comparison
        langs_a = {l.strip().lower() for l in player_a.languages}
        langs_b = {l.strip().lower() for l in player_b.languages}
        shared_langs = langs_a.intersection(langs_b)

        if shared_langs:
            lang_score = 100.0
            lang_assessment = f"Shared fluent communication in: {', '.join(sorted(shared_langs))}."
        else:
            lang_score = 0.0
            lang_assessment = f"Zero shared languages (A: {', '.join(langs_a)} vs. B: {', '.join(langs_b)}); severe barrier."

        results.append(
            DimensionScore(
                dimension="Language",
                score=round(lang_score, 1),
                weight=w.language_weight,
                assessment=lang_assessment,
            )
        )

        # 7. Schedule Comparison
        sched_a = set(player_a.schedule_slots)
        sched_b = set(player_b.schedule_slots)

        if not sched_a and not sched_b:
            sched_score = 75.0
            sched_assessment = "No fixed schedule constraints declared; flexible availability assumed."
        elif not sched_a or not sched_b:
            sched_score = 65.0
            sched_assessment = "One player has open availability; moderate schedule flexibility."
        else:
            overlap = sched_a.intersection(sched_b)
            union = sched_a.union(sched_b)
            ratio = len(overlap) / len(union) if union else 1.0
            sched_score = max(10.0, min(100.0, ratio * 100.0))
            sched_assessment = (
                f"Strong schedule overlap ({len(overlap)} matching time blocks)."
                if ratio >= 0.5
                else f"Low schedule overlap ({len(overlap)} shared blocks); limited gaming hours together."
            )

        results.append(
            DimensionScore(
                dimension="Schedule",
                score=round(sched_score, 1),
                weight=w.schedule_weight,
                assessment=sched_assessment,
            )
        )

        return results


class CompetitiveEvaluator:
    """Evaluates official rank disparity, win-rate parity, and role complementarity."""

    def evaluate(
        self,
        player_a: PlayerComparisonInput,
        player_b: PlayerComparisonInput,
        config: AICompatibilityConfig,
    ) -> list[DimensionScore]:
        w = config.weights
        results: list[DimensionScore] = []

        # 8. Official Rank Comparison
        rating_a = player_a.rank_rating if player_a.rank_rating is not None else 1000
        rating_b = player_b.rank_rating if player_b.rank_rating is not None else 1000
        mmr_diff = abs(rating_a - rating_b)
        # Scaled so that <= 150 MMR diff is 100%, 500 diff is ~60%, 1000 diff is ~20%
        rank_score = max(10.0, min(100.0, 100.0 - (mmr_diff / 10.0)))
        rank_assessment = (
            f"Tight rank parity ({mmr_diff} MMR delta); balanced skill lobby."
            if mmr_diff <= 200
            else f"Noticeable rank gap ({mmr_diff} MMR delta); potential matchmaking lobby strain."
        )

        results.append(
            DimensionScore(
                dimension="Official Rank",
                score=round(rank_score, 1),
                weight=w.rank_weight,
                assessment=rank_assessment,
            )
        )

        # 9. Win Rate Comparison
        wr_a = player_a.win_rate if player_a.win_rate is not None else 50.0
        wr_b = player_b.win_rate if player_b.win_rate is not None else 50.0
        wr_diff = abs(wr_a - wr_b)
        wr_score = max(20.0, min(100.0, 100.0 - (wr_diff * 4.0)))
        wr_assessment = (
            f"Similar competitive win rates ({wr_a:.1f}% vs. {wr_b:.1f}%)."
            if wr_diff <= 6.0
            else f"Win rate divergence ({wr_a:.1f}% vs. {wr_b:.1f}%); tilt vulnerability under losses."
        )

        results.append(
            DimensionScore(
                dimension="Win Rate",
                score=round(wr_score, 1),
                weight=w.win_rate_weight,
                assessment=wr_assessment,
            )
        )

        # 10. Preferred Role Comparison (Complementary vs. Clash)
        roles_a = [r.strip().lower() for r in player_a.preferred_roles]
        roles_b = [r.strip().lower() for r in player_b.preferred_roles]

        if not roles_a or not roles_b:
            role_score = 80.0
            role_assessment = "Unspecified role preferences; flexible role assignment likely."
        else:
            overlap = set(roles_a).intersection(set(roles_b))
            if overlap and len(roles_a) == 1 and len(roles_b) == 1:
                # Direct one-trick collision
                role_score = 30.0
                role_assessment = f"Direct role clash on '{roles_a[0]}'; both players prefer the exact same position."
            elif overlap:
                # Overlap exists but players have secondary/flex roles
                role_score = 75.0
                role_assessment = "Partial role overlap with flex adaptability available."
            else:
                # Completely complementary (e.g. Duelist + Controller)
                role_score = 100.0
                role_assessment = f"Ideal role synergy ({', '.join(roles_a)} paired with {', '.join(roles_b)})."

        results.append(
            DimensionScore(
                dimension="Preferred Role",
                score=round(role_score, 1),
                weight=w.role_weight,
                assessment=role_assessment,
            )
        )

        return results
