"""
Template Catalogue for AI Explanation Engine.
Provides modular natural language generation (NLG) templates with dynamic parameter slots.
"""

from typing import Any

# ==============================================================================
# 1. WHY TWO PLAYERS MATCH (Synergies & Alignment)
# ==============================================================================

MATCH_TEMPLATES: dict[str, list[str]] = {
    "leadership_complementary": [
        "{leader} provides decisive tactical shotcalling ({lead_score:.0f}/100), while {follower} focuses on seamless execution and tactical support ({foll_score:.0f}/100), creating an optimal command hierarchy without ego friction.",
        "Clear in-game hierarchy: {leader} naturally anchors calling while {follower} bolsters round execution with minimal conflict.",
    ],
    "communication_alignment": [
        "Both {player_a} ({comms_a:.0f}/100) and {player_b} ({comms_b:.0f}/100) maintain vocal callout cadences, ensuring high round-to-round situational awareness and rapid information exchange.",
        "Exceptional verbal synergy: High mutual communication ratings enable instant mid-round rotates and utility synchronization.",
    ],
    "aggression_harmony": [
        "Balanced combat pacing: {aggr_player} ({aggr_score:.0f}/100) drives entry engagements and space creation, while {support_player} ({supp_score:.0f}/100) trades frags and anchors retakes.",
        "Complementary tempo: High-pressure frontline initiation paired with measured backline support gives the duo reliable execute stability.",
    ],
    "role_synergy": [
        "Tactical role synergy: {player_a} playing {role_a} and {player_b} on {role_b} cover core tactical requirements, providing both front-foot aggression and area control.",
        "Cohesive agent pool: {role_a} and {role_b} form an established competitive core that avoids utility redundancies.",
    ],
    "skill_parity": [
        "Close competitive skill alignment (MMR delta: {mmr_delta} pts): Both players share equivalent lobby game sense, mechanical expectations, and match pacing.",
        "Skill bracket parity: Similar rank tiers ({rank_a} & {rank_b}) ensure balanced matchmaking placement and mutual confidence.",
    ],
    "logistics_alignment": [
        "Regional and schedule harmony: Shared low-latency server region ({region}) and synchronized playtimes facilitate consistent queue sessions.",
    ],
}

# ==============================================================================
# 2. WHY THEY DON'T MATCH (Friction & Disconnects)
# ==============================================================================

MISMATCH_TEMPLATES: dict[str, list[str]] = {
    "dual_leadership_clash": [
        "Dual-shotcaller friction: Both {player_a} ({lead_a:.0f}/100) and {player_b} ({lead_b:.0f}/100) possess dominant leadership tendencies, introducing high risk of competing mid-round calls and strategic gridlock.",
        "Leadership collision: Dual high-assertiveness playstyles often lead to conflicting executes during high-pressure rounds.",
    ],
    "rudderless_squad": [
        "Absence of decisive shotcalling: Neither player assumes proactive round leadership (max leadership: {max_lead:.0f}/100), which may leave mid-round adaptations uncoordinated.",
    ],
    "communication_deficit": [
        "Sub-optimal verbal communication: Low combined voice activity ({comms_a:.0f} & {comms_b:.0f}/100) risks silent rounds, missed trade opportunities, and delayed flank warnings.",
        "Communication gap: One or both players rely primarily on passive pings rather than actionable verbal callouts.",
    ],
    "aggression_disconnect": [
        "Pacing disparity: Wide aggression delta ({delta_aggr:.0f} pts) risks desynchronized engages, with {aggr_player} overextending while {passive_player} holds passive angles.",
    ],
    "role_collision": [
        "Primary role collision: Both {player_a} and {player_b} specialize exclusively in {role}, creating contest over agent picks and leaving complementary support roles unfulfilled.",
    ],
    "skill_disparity": [
        "Noticeable skill disparity ({mmr_delta} MMR gap between {rank_a} and {rank_b}): Discrepancies in mechanical pace or game tempo can lead to mismatched lobby expectations or frustration.",
    ],
    "logistics_mismatch": [
        "Logistical barrier: Divergent server regions ({reg_a} vs {reg_b}) or non-overlapping schedules impede reliable team play.",
    ],
    "language_barrier": [
        "Language disconnect: Lack of a common fluent language severely hinders real-time voice coordination under competitive pressure.",
    ],
}

# ==============================================================================
# 3. STANDOUT STRENGTHS NARRATIVE
# ==============================================================================

STRENGTHS_TEMPLATES: dict[str, str] = {
    "role_diversity": "Diverse tactical toolset: Flexible coverage between {role_a} and {role_b} enables versatile offensive site executes and defensive lockdown setups.",
    "verbal_coordination": "Proactive information network: Consistent callouts and clear vocal cues keep both players ahead of enemy rotates.",
    "command_clarity": "Structured command dynamic: An unambiguous shotcaller ({leader}) paired with a disciplined teammate ({follower}) prevents hesitation in clutch rounds.",
    "frontline_anchor_dynamic": "Asymmetric combat pacing: Entry-fragger space creation backed by reliable post-plant anchor utility guarantees strong trades.",
    "shared_schedule": "Cohesive availability: Overlapping gaming windows foster team continuity and progressive tactical synergy over extended sessions.",
    "lobby_parity": "Lobby balance parity: Comparable rank ratings eliminate rank disparity penalties and ensure balanced matchmaking opposition.",
}

# ==============================================================================
# 4. WEAKNESSES NARRATIVE
# ==============================================================================

WEAKNESSES_TEMPLATES: dict[str, str] = {
    "ego_tension": "Vulnerability to shotcall disputes: Heated late-round macro decisions can generate friction when both players demand the final say.",
    "silent_collapse": "Information bottlenecks: Reluctance to call enemy utility or health states during hectic firefights creates blind spots.",
    "trade_lag": "Desynchronized trading: Aggressive pushes without immediate backline flash or smoke assistance leave entry attempts isolated.",
    "pool_overlap": "Restricted flexibility: Simultaneous preference for {role} limits adaptation when team compositions require tactical flex.",
    "rank_tilt": "Skill expectation friction: Large gap in win rates ({wr_a:.1f}% vs {wr_b:.1f}%) or ranks can foster blame-shifting during losing streaks.",
    "schedule_fragmentation": "Fragmented play windows: Infrequent overlapping sessions make establishing consistent duo chemistry challenging.",
}

# ==============================================================================
# 5. IMPROVEMENT & COACHING SUGGESTIONS
# ==============================================================================

IMPROVEMENT_TEMPLATES: dict[str, str] = {
    "shotcaller_protocol": "Pre-define default In-Game Leader (IGL) responsibilities during buy phase; assign secondary player to focus on micro-trades and utility support.",
    "comms_cadence": "Implement a standardized 3-second callout rule (Agent, Location, Health/Utility) to maintain clean voice comms during rounds.",
    "role_flexing": "Cross-train secondary roles: Have {primary_user} or {secondary_user} expand into a flex archetype (e.g. Initiator or Controller) to avoid pick conflicts.",
    "buddy_spacing": "Calibrate entry spacing: Maintain a strict 2-meter proximity buffer during site pushes to ensure guaranteed revenge frags within 1.5 seconds.",
    "crosshair_trade_drills": "Warm up together with 10 minutes of duo Deathmatch or Retake drills focusing on synchronized peeking and cross-firing.",
    "schedule_anchor": "Establish 2 dedicated recurring weekly duo sessions to build repeatable playstyle habits without schedule friction.",
}
