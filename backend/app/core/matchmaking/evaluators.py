"""
Specialized Evaluators for Matchmaking & Squad Recommendation:
- SkillEvaluator: Rank, MMR disparity, and win-rate parity
- TeamBalanceEvaluator: Archetype coverage, role clash detection, and missing roles
- CommunicationEvaluator: Comms score symmetry and language intersection
- ScheduleRegionEvaluator: Availability overlap, server region latency, and preferred games
"""

import math
from typing import Sequence

from app.schemas.matchmaking import MatchmakingCandidate

# Core tactical roles for competitive games (Valorant, CS2, Dota 2)
TACTICAL_ROLES: list[str] = [
    "Leader",
    "Support",
    "Duelist",
    "Sentinel",
    "Strategist",
    "Controller",
]

# Ideal 5-player role template (1 IGL, 1 Entry/Duelist, 1 Smokes/Controller, 1 Anchor/Sentinel, 1 Support/Flex)
ESSENTIAL_ROLES: set[str] = {"Leader", "Duelist", "Controller", "Sentinel", "Support"}


class SkillEvaluator:
    """Evaluates competitive parity, MMR divergence, and win-rate symmetry."""

    @staticmethod
    def evaluate_pair(
        player_a: MatchmakingCandidate,
        player_b: MatchmakingCandidate,
    ) -> tuple[float, list[str], list[str]]:
        reasons: list[str] = []
        warnings: list[str] = []

        mmr_a = player_a.mmr
        mmr_b = player_b.mmr
        delta_mmr = abs(mmr_a - mmr_b)

        # Non-linear skill drop-off: within 200 MMR is ideal parity
        if delta_mmr <= 150:
            skill_score = 100.0
            reasons.append(f"Near-identical competitive tier ({player_a.rank or 'Unranked'} vs {player_b.rank or 'Unranked'}).")
        elif delta_mmr <= 350:
            skill_score = round(100.0 - (delta_mmr - 150) * 0.15, 2)
            reasons.append("Comparable competitive skill level within 1 tier.")
        elif delta_mmr <= 650:
            skill_score = round(70.0 - (delta_mmr - 350) * 0.10, 2)
            warnings.append(f"Noticeable skill disparity ({delta_mmr} MMR delta); gameplay pace may differ.")
        else:
            skill_score = max(10.0, round(40.0 - (delta_mmr - 650) * 0.05, 2))
            warnings.append(f"Significant competitive rank gap ({player_a.rank or 'Tier A'} vs {player_b.rank or 'Tier B'}); exceeds standard queue tolerance.")

        # Win rate parity check
        wr_delta = abs(player_a.win_rate - player_b.win_rate)
        if wr_delta <= 5.0:
            reasons.append(f"Matched win percentages ({player_a.win_rate:.1f}% vs {player_b.win_rate:.1f}%).")

        return skill_score, reasons, warnings

    @staticmethod
    def evaluate_squad_variance(members: Sequence[MatchmakingCandidate]) -> tuple[float, list[str], list[str]]:
        if not members:
            return 0.0, [], []

        mmrs = [m.mmr for m in members]
        mean_mmr = sum(mmrs) / len(mmrs)
        variance = sum((x - mean_mmr) ** 2 for x in mmrs) / len(mmrs)
        std_dev = round(math.sqrt(variance), 1)

        reasons: list[str] = []
        warnings: list[str] = []

        if std_dev <= 120.0:
            reasons.append(f"Exceptional squad ELO cohesion (average MMR {int(mean_mmr)}, std dev {std_dev}).")
        elif std_dev >= 300.0:
            warnings.append(f"High squad skill spread (MMR standard deviation {std_dev}); lower-tier members may face challenging matchups.")

        return std_dev, reasons, warnings


class TeamBalanceEvaluator:
    """Evaluates archetype diversity, detects missing roles, and identifies role clashes."""

    @staticmethod
    def evaluate_pair_synergy(
        player_a: MatchmakingCandidate,
        player_b: MatchmakingCandidate,
    ) -> tuple[float, list[str], list[str]]:
        reasons: list[str] = []
        warnings: list[str] = []

        role_a = player_a.primary_role
        role_b = player_b.primary_role

        # Natural complementary pairs
        complementary_pairs = {
            frozenset(["Leader", "Duelist"]): ("Vocal shotcaller coordinates aggressive entry duels.", 95.0),
            frozenset(["Leader", "Support"]): ("Tactical IGL and selfless support maintain squad structure and morale.", 95.0),
            frozenset(["Leader", "Controller"]): ("Leader dictates site hits layered with precise smoke lines.", 92.0),
            frozenset(["Leader", "Strategist"]): ("Grandmaster macro planning combined with active in-game calls.", 92.0),
            frozenset(["Leader", "Sentinel"]): ("Commander pairs with defensive anchor for lockdown defense.", 90.0),
            frozenset(["Duelist", "Controller"]): ("Duelist capitalizes on vision denial and space created by Controller.", 92.0),
            frozenset(["Duelist", "Support"]): ("Support enables entry duelist with peeling, flashes, and trades.", 94.0),
            frozenset(["Sentinel", "Controller"]): ("Full map spatial control with lockdown traps and vision denial.", 88.0),
            frozenset(["Sentinel", "Support"]): ("High defensive resilience and sustained crossfire trading.", 86.0),
            frozenset(["Strategist", "Controller"]): ("Surgical utility choreography and calculated map rotations.", 90.0),
        }

        pair_key = frozenset([role_a, role_b])

        if role_a == role_b:
            if role_a == "Leader":
                synergy_score = 45.0
                warnings.append("Both players are primary Leaders; multiple vocal shotcallers can create command friction.")
            elif role_a == "Duelist":
                synergy_score = 65.0
                warnings.append("Both players specialize as Duelists; ensures high aggression but may compete for entry utility.")
            elif role_a in ["Controller", "Sentinel", "Support"]:
                synergy_score = 75.0
                reasons.append(f"Shared focus on defensive utility ({role_a}).")
            else:
                synergy_score = 70.0
        elif pair_key in complementary_pairs:
            desc, score = complementary_pairs[pair_key]
            synergy_score = score
            reasons.append(desc)
        else:
            synergy_score = 80.0
            reasons.append(f"Balanced role pairing ({role_a} + {role_b}).")

        # Factor in secondary role adaptability
        if player_a.secondary_role and player_a.secondary_role != role_b:
            synergy_score = min(100.0, synergy_score + 5.0)

        return round(synergy_score, 1), reasons, warnings

    @staticmethod
    def evaluate_squad_composition(
        members: Sequence[MatchmakingCandidate],
        target_size: int = 5,
    ) -> tuple[float, dict[str, int], list[str], list[str], list[str]]:
        role_counts: dict[str, int] = {role: 0 for role in TACTICAL_ROLES}
        for m in members:
            p_role = m.primary_role if m.primary_role in role_counts else "Support"
            role_counts[p_role] += 1

        reasons: list[str] = []
        warnings: list[str] = []

        # Check for missing essential roles
        missing_roles: list[str] = []
        for role in ["Leader", "Duelist", "Controller", "Sentinel", "Support"]:
            if role_counts[role] == 0:
                missing_roles.append(role)

        # Check role clashes
        if role_counts["Leader"] > 1:
            warnings.append(f"Multiple primary Leaders ({role_counts['Leader']}) present; designate a single shotcaller to prevent mid-round call conflicts.")
        elif role_counts["Leader"] == 1:
            reasons.append("Dedicated In-Game Leader (Shotcaller) anchored.")

        if role_counts["Duelist"] > 2:
            warnings.append("Squad has 3+ Duelists; risk of insufficient defensive utility and smoke coverage.")
        elif role_counts["Duelist"] in (1, 2):
            reasons.append(f"Optimal entry duel capacity ({role_counts['Duelist']} Duelist).")

        if role_counts["Controller"] >= 1:
            reasons.append("Vision control secured with dedicated Controller smokes.")
        else:
            warnings.append("Missing Controller: squad lacks vision denial and smoke utility.")

        if role_counts["Sentinel"] >= 1:
            reasons.append("Perimeter defense and flank anchor covered by Sentinel.")

        # Compute balance percentage based on archetype diversity
        unique_roles = sum(1 for count in role_counts.values() if count > 0)
        base_balance = (unique_roles / min(target_size, len(TACTICAL_ROLES))) * 100.0

        # Penalize excessive duplicate roles
        penalty = 0.0
        for count in role_counts.values():
            if count > 2:
                penalty += (count - 2) * 15.0

        balance_pct = round(max(20.0, min(100.0, base_balance - penalty)), 1)
        return balance_pct, role_counts, missing_roles, reasons, warnings


class CommunicationEvaluator:
    """Evaluates communication scores, voice callout styles, and language compatibility."""

    @staticmethod
    def evaluate(
        player_a: MatchmakingCandidate,
        player_b: MatchmakingCandidate,
    ) -> tuple[float, list[str], list[str]]:
        reasons: list[str] = []
        warnings: list[str] = []

        # 1. Language intersection check
        shared_langs = set(player_a.languages).intersection(set(player_b.languages))
        if shared_langs:
            lang_score = 100.0
            reasons.append(f"Shared spoken communication: {', '.join(sorted(shared_langs))}.")
        else:
            lang_score = 15.0
            warnings.append(
                f"Language mismatch ({player_a.languages} vs {player_b.languages}); real-time voice callouts will be limited."
            )

        # 2. Communication score synergy
        comms_a = player_a.communication
        comms_b = player_b.communication
        avg_comms = (comms_a + comms_b) / 2.0
        comms_delta = abs(comms_a - comms_b)

        if comms_a >= 70 and comms_b >= 70:
            comm_score = 95.0
            reasons.append("Both players maintain high-frequency tactical voice callouts.")
        elif comms_delta >= 40:
            comm_score = 65.0
            warnings.append("Asymmetric communication styles: one player is highly vocal while the other communicates reservedly.")
        else:
            comm_score = max(50.0, avg_comms)

        # Blended communication rating (60% comms style, 40% language match)
        blended = round(0.60 * comm_score + 0.40 * lang_score, 1)
        return blended, reasons, warnings


class ScheduleRegionEvaluator:
    """Evaluates availability schedule overlap, server region latency, and game preferences."""

    @staticmethod
    def evaluate(
        player_a: MatchmakingCandidate,
        player_b: MatchmakingCandidate,
    ) -> tuple[float, float, float, list[str], list[str]]:
        reasons: list[str] = []
        warnings: list[str] = []

        # Region match
        if player_a.region.lower() == player_b.region.lower():
            region_score = 100.0
            reasons.append(f"Identical server region ({player_a.region}); lowest possible network ping.")
        else:
            # Check continent/neighboring subregions
            reg_a = player_a.region.lower()
            reg_b = player_b.region.lower()
            if ("na" in reg_a and "na" in reg_b) or ("eu" in reg_a and "eu" in reg_b) or ("ap" in reg_a and "ap" in reg_b):
                region_score = 75.0
                reasons.append(f"Adjacent server regions ({player_a.region} and {player_b.region}); acceptable latency.")
            else:
                region_score = 25.0
                warnings.append(f"Cross-region match ({player_a.region} vs {player_b.region}); may experience elevated ping.")

        # Schedule overlap
        overlap_tags = set(player_a.schedule_tags).intersection(set(player_b.schedule_tags))
        if overlap_tags:
            schedule_score = 100.0
            reasons.append(f"Compatible gaming schedule: {', '.join(sorted(overlap_tags))}.")
        else:
            schedule_score = 40.0
            warnings.append("Differing preferred availability windows; scheduling synchronized sessions may require planning.")

        # Preferred games
        shared_games = set(player_a.preferred_games).intersection(set(player_b.preferred_games))
        if shared_games:
            game_score = 100.0
            reasons.append(f"Common game interests: {', '.join(sorted(shared_games))}.")
        else:
            game_score = 30.0
            warnings.append(f"Differing main games ({player_a.preferred_games} vs {player_b.preferred_games}).")

        return schedule_score, region_score, game_score, reasons, warnings
