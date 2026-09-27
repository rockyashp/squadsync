"""
Unit and integration tests for Matchmaking Engine:
- Rank-to-MMR normalization
- Skill disparity, team balance, missing roles, and communication evaluators
- Full MatchmakingEngine pairwise compatibility scoring with reasons and warnings
- SquadOptimizer combinatorial recommendation
- FastAPI REST endpoints (/compatibility, /recommend-squad, /evaluate-team)
"""

import uuid
from httpx import AsyncClient
import pytest

from app.core.matchmaking.engine import MatchmakingEngine, SquadOptimizer
from app.core.matchmaking.evaluators import (
    CommunicationEvaluator,
    ScheduleRegionEvaluator,
    SkillEvaluator,
    TeamBalanceEvaluator,
)
from app.core.matchmaking.rank_scaler import normalize_rank_to_mmr
from app.schemas.matchmaking import MatchmakingCandidate


# ==============================================================================
# 1. Rank Scaler Tests
# ==============================================================================

def test_rank_scaler_normalization():
    """Verify rank string to ELO conversion across multiple publisher formats."""
    # Valorant / Generic
    assert normalize_rank_to_mmr("Iron 1") == 1000
    assert normalize_rank_to_mmr("Silver 2") == 1400 + 60
    assert normalize_rank_to_mmr("Diamond 3", rank_rating=50) == 2300 + 120 + 50
    assert normalize_rank_to_mmr("Radiant") >= 3300

    # Dota 2 medals
    assert normalize_rank_to_mmr("Herald 3") >= 1000
    assert normalize_rank_to_mmr("Archon 1") == 1800
    assert normalize_rank_to_mmr("Immortal") >= 2900

    # CS2 Premier / Tiers
    assert normalize_rank_to_mmr("Global Elite") == 3200
    premier_mmr = normalize_rank_to_mmr("18,500")
    assert 2000 <= premier_mmr <= 3000

    # Unranked / empty fallback
    assert normalize_rank_to_mmr(None) == 1500
    assert normalize_rank_to_mmr("") == 1500


# ==============================================================================
# 2. Evaluator Component Tests
# ==============================================================================

def _make_candidate(
    name: str,
    role: str = "Duelist",
    secondary: str | None = None,
    rank: str = "Diamond 1",
    mmr: int = 2300,
    win_rate: float = 54.0,
    comms: int = 80,
    region: str = "NA-East",
    languages: list[str] | None = None,
    schedules: list[str] | None = None,
    games: list[str] | None = None,
) -> MatchmakingCandidate:
    return MatchmakingCandidate(
        user_id=uuid.uuid4(),
        username=name,
        primary_role=role,
        secondary_role=secondary,
        rank=rank,
        mmr=mmr,
        win_rate=win_rate,
        communication=comms,
        leadership=75 if role == "Leader" else 50,
        strategy=75 if role in ["Strategist", "Controller"] else 50,
        teamwork=75 if role in ["Support", "Sentinel"] else 50,
        aggression=85 if role == "Duelist" else 45,
        region=region,
        languages=languages or ["en"],
        schedule_tags=schedules or ["evenings", "weekends"],
        preferred_games=games or ["Valorant", "CS2"],
    )


def test_skill_evaluator_parity_and_gaps():
    """Verify SkillEvaluator awards high scores to close ranks and flags wide MMR disparities."""
    p1 = _make_candidate("Ace", mmr=2300, rank="Diamond 1")
    p2 = _make_candidate("Bravo", mmr=2350, rank="Diamond 1")
    p3 = _make_candidate("Rookie", mmr=1200, rank="Bronze 1")

    # Near identical tier
    score_close, reasons, warns = SkillEvaluator.evaluate_pair(p1, p2)
    assert score_close == 100.0
    assert any("tier" in r.lower() for r in reasons)
    assert len(warns) == 0

    # Wide gap (Diamond 1 vs Bronze 1)
    score_wide, _, warns_wide = SkillEvaluator.evaluate_pair(p1, p3)
    assert score_wide < 50.0
    assert any("rank gap" in w.lower() or "disparity" in w.lower() for w in warns_wide)


def test_team_balance_and_missing_roles():
    """Verify TeamBalanceEvaluator computes balance %, detects missing roles, and flags clashes."""
    igl = _make_candidate("IGL", role="Leader")
    duelist = _make_candidate("Entry", role="Duelist")
    smokes = _make_candidate("Smokes", role="Controller")
    anchor = _make_candidate("Anchor", role="Sentinel")
    support = _make_candidate("Medic", role="Support")

    # 1. Ideal balanced squad
    squad_perfect = [igl, duelist, smokes, anchor, support]
    balance_pct, distribution, missing, reasons, warns = TeamBalanceEvaluator.evaluate_squad_composition(squad_perfect)

    assert balance_pct >= 90.0
    assert len(missing) == 0
    assert any("shotcaller" in r.lower() for r in reasons)
    assert any("vision control" in r.lower() for r in reasons)

    # 2. Imbalanced squad (3 Duelists, 2 Leaders - Missing Controller, Sentinel, Support)
    squad_flawed = [
        _make_candidate("Lead1", role="Leader"),
        _make_candidate("Lead2", role="Leader"),
        _make_candidate("D1", role="Duelist"),
        _make_candidate("D2", role="Duelist"),
        _make_candidate("D3", role="Duelist"),
    ]
    balance_bad, _, missing_bad, _, warns_bad = TeamBalanceEvaluator.evaluate_squad_composition(squad_flawed)
    assert balance_bad < 60.0
    assert "Controller" in missing_bad
    assert "Sentinel" in missing_bad
    assert "Support" in missing_bad
    assert any("multiple" in w.lower() and "leader" in w.lower() for w in warns_bad)
    assert any("3+" in w.lower() or "duelists" in w.lower() for w in warns_bad)


def test_communication_and_language_evaluator():
    """Verify CommunicationEvaluator detects high comms synergy and language barriers."""
    p_en1 = _make_candidate("VocalUS", comms=85, languages=["en"])
    p_en2 = _make_candidate("VocalUK", comms=90, languages=["en"])
    p_es = _make_candidate("SoloES", comms=35, languages=["es"])

    # High comms + shared language
    score_good, reasons, _ = CommunicationEvaluator.evaluate(p_en1, p_en2)
    assert score_good >= 90.0
    assert any("shared spoken" in r.lower() for r in reasons)
    assert any("high-frequency" in r.lower() for r in reasons)

    # Language mismatch + asymmetric comms
    score_bad, _, warns = CommunicationEvaluator.evaluate(p_en1, p_es)
    assert score_bad < 60.0
    assert any("language mismatch" in w.lower() for w in warns)
    assert any("asymmetric" in w.lower() for w in warns)


def test_schedule_and_region_evaluator():
    """Verify ScheduleRegionEvaluator scores latency and availability windows."""
    p_na1 = _make_candidate("US1", region="NA-East", schedules=["evenings"])
    p_na2 = _make_candidate("US2", region="NA-East", schedules=["evenings", "weekends"])
    p_asia = _make_candidate("Asia1", region="AP-South", schedules=["mornings"])

    # Same region and overlapping schedule
    sched_score, reg_score, game_score, reasons, _ = ScheduleRegionEvaluator.evaluate(p_na1, p_na2)
    assert sched_score == 100.0
    assert reg_score == 100.0
    assert game_score == 100.0

    # Cross-region and differing schedule
    sched_diff, reg_diff, _, _, warns = ScheduleRegionEvaluator.evaluate(p_na1, p_asia)
    assert sched_diff < 50.0
    assert reg_diff <= 25.0
    assert any("cross-region" in w.lower() for w in warns)


# ==============================================================================
# 3. Matchmaking Engine & Optimizer Integration Tests
# ==============================================================================

def test_engine_pairwise_compatibility():
    """Test MatchmakingEngine produces granular breakdown, percentage, reasons, and warnings."""
    engine = MatchmakingEngine()
    player_a = _make_candidate("ViperMain", role="Controller", mmr=2300, comms=85)
    player_b = _make_candidate("JettMain", role="Duelist", mmr=2350, comms=80)

    res = engine.evaluate_pair(player_a, player_b)
    assert res.player_a_username == "ViperMain"
    assert res.player_b_username == "JettMain"
    assert res.overall_compatibility_pct >= 85.0

    # Verify breakdown fields
    assert res.breakdown.role_synergy >= 90.0
    assert res.breakdown.skill_alignment >= 95.0
    assert res.breakdown.communication_match >= 85.0
    assert res.breakdown.region_match == 100.0
    assert len(res.reasons) >= 2


def test_squad_optimizer_selection():
    """Test SquadOptimizer selects high-balance squad compositions from a candidate pool."""
    requester = _make_candidate("Me", role="Leader", mmr=2100)
    candidates = [
        _make_candidate("Duelist1", role="Duelist", mmr=2150),
        _make_candidate("Duelist2", role="Duelist", mmr=2100),
        _make_candidate("Smokes", role="Controller", mmr=2050),
        _make_candidate("Anchor", role="Sentinel", mmr=2100),
        _make_candidate("Support1", role="Support", mmr=2120),
        _make_candidate("Lead2", role="Leader", mmr=1800),  # Conflicting role
    ]

    optimizer = SquadOptimizer()
    top_squads = optimizer.recommend_squads(
        requester=requester,
        candidates=candidates,
        game_name="Valorant",
        squad_size=5,
        top_k=2,
    )

    assert len(top_squads) >= 1
    best_squad = top_squads[0]
    assert best_squad.squad_size == 5
    assert best_squad.compatibility_pct >= 75.0
    assert best_squad.team_balance_pct >= 80.0
    # Top squad should include the necessary roles (Controller, Sentinel, Support, Duelist)
    assert "Controller" not in best_squad.missing_roles


# ==============================================================================
# 4. FastAPI Endpoint Integration Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_matchmaking_compatibility_api(authenticated_client: AsyncClient, mock_user):
    """Test POST /api/v1/matchmaking/compatibility returns 200 with breakdown."""
    target_id = uuid.uuid4()
    payload = {
        "target_user_id": str(target_id),
        "game_name": "Valorant",
    }
    response = await authenticated_client.post("/api/v1/matchmaking/compatibility", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    result = data["data"]
    assert "overall_compatibility_pct" in result
    assert "breakdown" in result
    assert "reasons" in result
    assert "warnings" in result
    assert result["breakdown"]["role_synergy"] >= 0


@pytest.mark.asyncio
async def test_matchmaking_recommend_squad_api(authenticated_client: AsyncClient):
    """Test POST /api/v1/matchmaking/recommend-squad returns 200 with top squads."""
    payload = {
        "game_name": "Valorant",
        "squad_size": 5,
        "candidate_limit": 20,
    }
    response = await authenticated_client.post("/api/v1/matchmaking/recommend-squad", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    result = data["data"]
    assert "top_squads" in result
    assert isinstance(result["top_squads"], list)


@pytest.mark.asyncio
async def test_matchmaking_evaluate_team_api(authenticated_client: AsyncClient):
    """Test POST /api/v1/matchmaking/evaluate-team returns team balance and missing roles."""
    p1 = uuid.uuid4()
    p2 = uuid.uuid4()
    p3 = uuid.uuid4()

    payload = {
        "user_ids": [str(p1), str(p2), str(p3)],
        "game_name": "Valorant",
    }
    response = await authenticated_client.post("/api/v1/matchmaking/evaluate-team", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    squad = data["data"]
    assert squad["squad_size"] == 3
    assert "team_balance_pct" in squad
    assert "missing_roles" in squad
    assert "role_distribution" in squad
    assert "warnings" in squad
    assert "reasons" in squad


@pytest.mark.asyncio
async def test_matchmaking_unauthenticated(client: AsyncClient):
    """Test matchmaking endpoints reject unauthenticated requests with 401."""
    payload = {"target_user_id": str(uuid.uuid4())}
    res = await client.post("/api/v1/matchmaking/compatibility", json=payload)
    assert res.status_code == 401
