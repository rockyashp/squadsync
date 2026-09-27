"""
Universal Competitive Rank to Numerical ELO / MMR Scaler.
Converts multi-publisher rank strings into standardized competitive ratings (1000 - 3500+ scale).
Supports Valorant, CS2, Dota 2, League of Legends, and generic tier hierarchies.
"""

import re

# Standardized ELO baseline reference tiers
_GENERIC_TIERS: dict[str, int] = {
    "iron": 1000,
    "bronze": 1200,
    "silver": 1400,
    "gold": 1700,
    "platinum": 2000,
    "plat": 2000,
    "diamond": 2300,
    "ascendant": 2600,
    "immortal": 2900,
    "radiant": 3300,
    "master": 2800,
    "grandmaster": 3100,
    "challenger": 3400,
}

# Dota 2 competitive medals
_DOTA_MEDALS: dict[str, int] = {
    "herald": 1000,
    "guardian": 1250,
    "crusader": 1500,
    "archon": 1800,
    "legend": 2100,
    "ancient": 2400,
    "divine": 2800,
    "immortal": 3300,
}

# CS2 Premier Rating / Skill Groups
_CS2_TIERS: dict[str, int] = {
    "silver i": 1000,
    "silver elite": 1300,
    "gold nova": 1600,
    "master guardian": 1900,
    "distinguished master guardian": 2200,
    "legendary eagle": 2500,
    "supreme": 2800,
    "global elite": 3200,
}


def normalize_rank_to_mmr(rank_str: object, rank_rating: object = 0) -> int:
    """
    Translates arbitrary rank strings and competitive points into a standardized ELO (1000 - 3500+).
    Falls back to a median baseline (1500 MMR) when rank is unranked, unspecified, or non-string.
    """
    if not isinstance(rank_str, str) or not rank_str.strip():
        try:
            rating_offset = int(rank_rating) if isinstance(rank_rating, (int, float)) else 0
        except Exception:
            rating_offset = 0
        return 1500 + min(max(rating_offset, 0), 500)

    clean = rank_str.strip().lower()

    # Check direct numeric MMR (e.g. CS2 Premier '14,500' or raw Dota MMR '3200')
    digits_only = re.sub(r"[^\d]", "", clean)
    if digits_only and len(digits_only) >= 4:
        raw_val = int(digits_only)
        # Scale CS2 Premier rating (5,000 - 30,000) to our scale
        if raw_val > 5000:
            return int(1000 + (raw_val / 30000.0) * 2500)
        # Direct Dota/Chess-style ELO (1000 - 5000)
        if 1000 <= raw_val <= 6000:
            return min(int(raw_val * 0.75), 3800)

    # Sub-tier extraction (e.g., 'Diamond 2' -> tier 2 adds offset)
    sub_tier = 1
    tier_match = re.search(r"(\d)", clean)
    if tier_match:
        sub_tier = int(tier_match.group(1))

    # Match against generic tiers
    base_mmr = 1500
    matched = False

    for tier_name, tier_mmr in _GENERIC_TIERS.items():
        if tier_name in clean:
            base_mmr = tier_mmr
            matched = True
            break

    if not matched:
        for medal_name, medal_mmr in _DOTA_MEDALS.items():
            if medal_name in clean:
                base_mmr = medal_mmr
                matched = True
                break

    if not matched:
        for cs_tier, cs_mmr in _CS2_TIERS.items():
            if cs_tier in clean:
                base_mmr = cs_mmr
                matched = True
                break

    # Add sub-tier points (Tier 1 = +0, Tier 2 = +60, Tier 3 = +120)
    sub_tier_offset = max(0, (sub_tier - 1) * 60)
    rr_offset = min(max(rank_rating, 0), 100)

    return base_mmr + sub_tier_offset + rr_offset
