"""
OpenDota API Provider Adapter implementation.
Integrates the OpenDota competitive statistics service for Dota 2:
- SteamID64 to 32-bit Dota 2 Account ID conversion
- MMR estimate and rank tier badge translation (Herald through Immortal)
- Win/Loss records and win rate calculation
- Favorite heroes analytics (most played, win rates)
- Recent matches telemetry (KDA, match ID, duration, victory outcome)
- Raw API response capture in JSONB structures
"""

import logging
from typing import Any
import httpx

from app.core.config import settings
from app.models.game_account import GameAccount
from app.providers.dto import (
    AccountVerificationResult,
    ProviderProfileData,
    ProviderStatsData,
    ProviderSyncResult,
)
from app.providers.exceptions import (
    ProviderAPIException,
    ProviderException,
    ProviderRateLimitException,
)
from app.providers.game_provider import GameProvider

logger = logging.getLogger("squadsync.providers.opendota")

DOTA2_ID_OFFSET = 76561197960265728

# Rank Tier prefix to Medal name mapping
RANK_TIER_MEDALS = {
    1: "Herald",
    2: "Guardian",
    3: "Crusader",
    4: "Archon",
    5: "Legend",
    6: "Ancient",
    7: "Divine",
    8: "Immortal",
}

# Standard Dota 2 Hero catalog mapping for fast name resolution
HERO_ID_NAME_MAP = {
    1: "Anti-Mage",
    2: "Axe",
    3: "Bane",
    4: "Bloodseeker",
    5: "Crystal Maiden",
    6: "Drow Ranger",
    7: "Earthshaker",
    8: "Juggernaut",
    9: "Mirana",
    10: "Morphling",
    11: "Shadow Fiend",
    12: "Phantom Lancer",
    13: "Puck",
    14: "Pudge",
    15: "Razor",
    16: "Sand King",
    17: "Storm Spirit",
    18: "Sven",
    19: "Tiny",
    20: "Vengeful Spirit",
    21: "Windranger",
    22: "Zeus",
    23: "Kunkka",
    25: "Lina",
    26: "Lion",
    27: "Shadow Shaman",
    28: "Slardar",
    29: "Tidehunter",
    30: "Witch Doctor",
    31: "Lich",
    32: "Riki",
    33: "Enigma",
    34: "Tinker",
    35: "Sniper",
    36: "Necrophos",
    37: "Warlock",
    38: "Beastmaster",
    39: "Queen of Pain",
    40: "Venomancer",
    41: "Faceless Void",
    42: "Wraith King",
    43: "Death Prophet",
    44: "Phantom Assassin",
    45: "Pugna",
    46: "Templar Assassin",
    47: "Viper",
    48: "Luna",
    49: "Dragon Knight",
    50: "Dazzle",
    51: "Clockwerk",
    52: "Leshrac",
    53: "Nature's Prophet",
    54: "Lifestealer",
    55: "Dark Seer",
    56: "Clinkz",
    57: "Omniknight",
    58: "Enchantress",
    59: "Huskar",
    60: "Night Stalker",
    61: "Broodmother",
    62: "Bounty Hunter",
    63: "Weaver",
    64: "Jakiro",
    65: "Batrider",
    66: "Chen",
    67: "Spectre",
    68: "Ancient Apparition",
    69: "Doom",
    70: "Ursa",
    71: "Spirit Breaker",
    72: "Gyrocopter",
    73: "Alchemist",
    74: "Invoker",
    75: "Silencer",
    76: "Outworld Destroyer",
    77: "Lycan",
    78: "Brewmaster",
    79: "Shadow Demon",
    80: "Lone Druid",
    81: "Chaos Knight",
    82: "Meepo",
    83: "Treant Protector",
    84: "Ogre Magi",
    85: "Undying",
    86: "Rubick",
    87: "Disruptor",
    88: "Nyx Assassin",
    89: "Naga Siren",
    90: "Keeper of the Light",
    91: "Io",
    92: "Visage",
    93: "Slark",
    94: "Medusa",
    95: "Troll Warlord",
    96: "Centaur Warrunner",
    97: "Magnus",
    98: "Timbersaw",
    99: "Bristleback",
    100: "Tusk",
    101: "Skywrath Mage",
    102: "Abaddon",
    103: "Elder Titan",
    104: "Legion Commander",
    105: "Techies",
    106: "Ember Spirit",
    107: "Earth Spirit",
    108: "Underlord",
    109: "Terrorblade",
    110: "Phoenix",
    111: "Oracle",
    112: "Winter Wyvern",
    113: "Arc Warden",
    114: "Monkey King",
    119: "Dark Willow",
    120: "Pangolier",
    121: "Grimstroke",
    123: "Hoodwink",
    126: "Void Spirit",
    128: "Snapfire",
    129: "Mars",
    135: "Dawnbreaker",
    136: "Marci",
    137: "Primal Beast",
    138: "Muerta",
    145: "Ringmaster",
}


def steam_id64_to_dota_id(steam_id: str | int) -> int:
    """Convert 64-bit Steam ID into 32-bit Dota 2 Account ID."""
    try:
        val = int(str(steam_id).strip())
        if val > DOTA2_ID_OFFSET:
            return val - DOTA2_ID_OFFSET
        return val
    except ValueError:
        return 0


def dota_id_to_steam_id64(dota_id: int) -> str:
    """Convert 32-bit Dota 2 Account ID into 64-bit Steam ID string."""
    return str(dota_id + DOTA2_ID_OFFSET)


def format_rank_tier(rank_tier: int | None, leaderboard_rank: int | None = None) -> str:
    """Translate OpenDota rank_tier number into human-readable medal tier."""
    if not rank_tier or rank_tier == 0:
        return "Unranked"

    tier_digit = rank_tier // 10
    star_digit = rank_tier % 10

    medal = RANK_TIER_MEDALS.get(tier_digit, "Unranked")
    if medal == "Immortal":
        if leaderboard_rank:
            return f"Immortal #{leaderboard_rank}"
        return "Immortal"

    if star_digit > 0:
        return f"{medal} {star_digit}"
    return medal


class OpenDotaProvider(GameProvider):
    """
    Adapter integrating the OpenDota API to fetch competitive telemetry, MMR,
    rank badges, favorite heroes, and recent match performance for Dota 2.
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = (base_url or settings.OPENDOTA_BASE_URL).rstrip("/")
        self.api_key = api_key or settings.OPENDOTA_API_KEY
        self._client = http_client

    @property
    def platform_name(self) -> str:
        return "opendota"

    @property
    def supported_games(self) -> list[str]:
        return ["Dota 2"]

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is not None:
            return self._client
        return httpx.AsyncClient(timeout=15.0)

    def _build_params(self, extra_params: dict[str, Any] | None = None) -> dict[str, Any]:
        params = dict(extra_params or {})
        if self.api_key:
            params["api_key"] = self.api_key
        return params

    async def verify_account(
        self,
        account_identifier: str,
        auth_payload: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AccountVerificationResult:
        """
        Verify player account existence via OpenDota player lookup.
        """
        dota_id = steam_id64_to_dota_id(account_identifier)
        if dota_id <= 0:
            return AccountVerificationResult(
                is_valid=False,
                account_identifier=account_identifier,
                in_game_name="",
                error_message="Invalid Steam ID or Dota 2 Account ID",
            )

        try:
            profile = await self.fetch_profile(account_identifier)
            return AccountVerificationResult(
                is_valid=True,
                account_identifier=account_identifier,
                in_game_name=profile.in_game_name,
                region=profile.region,
                metadata={
                    "dota_account_id": dota_id,
                    "avatar_url": profile.avatar_url,
                    **profile.raw_data,
                },
            )
        except Exception as e:
            return AccountVerificationResult(
                is_valid=False,
                account_identifier=account_identifier,
                in_game_name="",
                error_message=f"OpenDota player verification failed: {str(e)}",
            )

    async def fetch_profile(
        self,
        account_identifier: str,
        region: str | None = None,
        **kwargs: Any,
    ) -> ProviderProfileData:
        """
        Retrieve Dota 2 player profile from OpenDota /players/{account_id}.
        """
        dota_id = steam_id64_to_dota_id(account_identifier)
        url = f"{self.base_url}/players/{dota_id}"
        client = await self._get_client()

        try:
            res = await client.get(url, params=self._build_params())
            if res.status_code == 429:
                raise ProviderRateLimitException("OpenDota API rate limit reached", platform="opendota")
            if res.status_code != 200:
                raise ProviderAPIException(
                    f"OpenDota API error: HTTP {res.status_code}", platform="opendota"
                )

            data = res.json()
            profile = data.get("profile") or {}
            in_game_name = profile.get("personaname") or f"DotaPlayer_{dota_id}"
            avatar_url = profile.get("avatarfull") or profile.get("avatar")
            country = profile.get("loccountrycode") or region

            return ProviderProfileData(
                account_identifier=str(account_identifier),
                in_game_name=in_game_name,
                region=country,
                avatar_url=avatar_url,
                raw_data=data,
            )
        except httpx.RequestError as e:
            raise ProviderAPIException(f"OpenDota network error: {e}", platform="opendota") from e

    async def fetch_stats(
        self,
        account_identifier: str,
        season: str | None = None,
        game_mode: str | None = None,
        region: str | None = None,
        **kwargs: Any,
    ) -> list[ProviderStatsData]:
        """
        Retrieve comprehensive Dota 2 competitive telemetry:
        - MMR estimate & rank medal
        - Win/Loss records
        - Top favorite heroes
        - Recent matches history
        """
        dota_id = steam_id64_to_dota_id(account_identifier)
        client = await self._get_client()

        # 1. Fetch player overview
        player_res = await client.get(
            f"{self.base_url}/players/{dota_id}", params=self._build_params()
        )
        player_data = player_res.json() if player_res.status_code == 200 else {}

        # 2. Fetch Win/Loss
        wl_res = await client.get(
            f"{self.base_url}/players/{dota_id}/wl", params=self._build_params()
        )
        wl_data = wl_res.json() if wl_res.status_code == 200 else {}

        # 3. Fetch Heroes
        heroes_res = await client.get(
            f"{self.base_url}/players/{dota_id}/heroes", params=self._build_params()
        )
        heroes_data = heroes_res.json() if heroes_res.status_code == 200 else []

        # 4. Fetch Recent Matches
        matches_res = await client.get(
            f"{self.base_url}/players/{dota_id}/recentMatches", params=self._build_params()
        )
        matches_data = matches_res.json() if matches_res.status_code == 200 else []

        # 5. Process competitive metrics
        wins = int(wl_data.get("win", 0))
        losses = int(wl_data.get("lose", 0))
        matches_played = wins + losses
        win_rate = round((wins / matches_played * 100), 2) if matches_played > 0 else 0.0

        rank_tier = player_data.get("rank_tier")
        leaderboard_rank = player_data.get("leaderboard_rank")
        rank_name = format_rank_tier(rank_tier, leaderboard_rank)

        mmr_estimate = player_data.get("mmr_estimate", {}).get("estimate")
        competitive_rank = player_data.get("competitive_rank")
        mmr = mmr_estimate or competitive_rank or (rank_tier * 60 if rank_tier else None)

        # 6. Process Favorite Heroes (Top 5)
        top_heroes = []
        for h in sorted(heroes_data, key=lambda x: int(x.get("games", 0)), reverse=True)[:5]:
            hero_id = int(h.get("hero_id", 0))
            h_games = int(h.get("games", 0))
            h_wins = int(h.get("win", 0))
            h_wr = round((h_wins / h_games * 100), 2) if h_games > 0 else 0.0
            top_heroes.append({
                "hero_id": hero_id,
                "hero_name": HERO_ID_NAME_MAP.get(hero_id, f"Hero #{hero_id}"),
                "games": h_games,
                "wins": h_wins,
                "win_rate": h_wr,
            })

        # 7. Process Recent Matches (Top 10)
        recent_matches = []
        total_kills, total_deaths, total_assists = 0, 0, 0
        for m in matches_data[:10]:
            m_id = m.get("match_id")
            h_id = int(m.get("hero_id", 0))
            kills = int(m.get("kills", 0))
            deaths = int(m.get("deaths", 0))
            assists = int(m.get("assists", 0))
            player_slot = int(m.get("player_slot", 0))
            radiant_win = bool(m.get("radiant_win"))

            is_radiant = player_slot < 128
            won = (is_radiant and radiant_win) or (not is_radiant and not radiant_win)

            total_kills += kills
            total_deaths += deaths
            total_assists += assists

            m_kda = round((kills + assists) / max(deaths, 1), 2)
            duration_minutes = round(int(m.get("duration", 0)) / 60, 1)

            recent_matches.append({
                "match_id": m_id,
                "hero_id": h_id,
                "hero_name": HERO_ID_NAME_MAP.get(h_id, f"Hero #{h_id}"),
                "kills": kills,
                "deaths": deaths,
                "assists": assists,
                "kda": m_kda,
                "won": won,
                "duration_minutes": duration_minutes,
                "start_time": m.get("start_time"),
            })

        num_recent = len(recent_matches)
        avg_kd = round(total_kills / max(total_deaths, 1), 2) if num_recent > 0 else None

        # Build raw storage payload with complete telemetry
        raw_telemetry = {
            "steam_id": str(account_identifier),
            "dota_account_id": dota_id,
            "player_name": player_data.get("profile", {}).get("personaname"),
            "avatar": player_data.get("profile", {}).get("avatarfull"),
            "mmr": mmr,
            "rank": rank_name,
            "rank_tier": rank_tier,
            "leaderboard_rank": leaderboard_rank,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "favorite_heroes": top_heroes,
            "recent_matches": recent_matches,
            "raw_player_api": player_data,
            "raw_wl_api": wl_data,
            "raw_heroes_api": heroes_data[:20],
            "raw_recent_matches_api": matches_data[:10],
        }

        stat = ProviderStatsData(
            season=season or "Current",
            game_mode=game_mode or "ranked",
            rank=rank_name,
            rank_tier=rank_tier,
            rank_rating=mmr,
            matches_played=matches_played,
            wins=wins,
            losses=losses,
            win_rate=win_rate,
            kd_ratio=avg_kd,
            raw_stats=raw_telemetry,
        )

        return [stat]

    async def sync(
        self,
        game_account: GameAccount,
        **kwargs: Any,
    ) -> ProviderSyncResult:
        """
        Perform complete Dota 2 telemetry synchronization via OpenDota.
        """
        try:
            profile = await self.fetch_profile(game_account.account_identifier, region=game_account.region)
            stats = await self.fetch_stats(game_account.account_identifier, region=game_account.region)
            return ProviderSyncResult(
                is_success=True,
                profile=profile,
                stats=stats,
            )
        except Exception as e:
            logger.error(f"OpenDota sync failed for {game_account.account_identifier}: {e}")
            return ProviderSyncResult(
                is_success=False,
                error_message=str(e),
            )
