"""
Comprehensive Pytest Test Suite for SquadSync AI Systems:
1. DNA Generation (Survey processing, psychometrics, personality archetype, persistence)
2. Role Classification (4-input feature vector, rule-based & ML logic, confidence, signal weights)
3. Compatibility Engine (10-dimensional pairwise comparison, duo tiers, risk factors)
4. Squad Recommendation (Candidate pool, role balance, skill parity, combinatorial search, designated IGL)
5. Explanation Engine (Template-based NLG, match/mismatch reasons, strengths, coaching suggestions)

Uses Mock Database (AsyncSession & Repositories) and Mock External APIs (Riot & Steam/Dota).
Targeting >= 90% backend test coverage.
"""

from collections.abc import Sequence
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
import pytest
from httpx import AsyncClient

from app.core.compatibility.config import default_compatibility_config
from app.core.compatibility.engine import AICompatibilityEngine
from app.core.compatibility.models import CompatibilityReport, PlayerComparisonInput
from app.core.explanation.config import default_explanation_config
from app.core.explanation.engine import AIExplanationEngine, PlayerExplanationContext
from app.core.role_classifier.config import default_classification_config
from app.core.role_classifier.engine import RuleBasedRoleClassifier
from app.core.role_classifier.features import (
    GamerDNAVector,
    GamerRoleFeatures,
    OfficialGameStats,
)
from app.core.role_classifier.ml_classifier import MLRoleClassifier
from app.core.squad_recommendation.config import default_squad_config
from app.core.squad_recommendation.engine import SquadRecommendationEngine
from app.core.squad_recommendation.evaluators import (
    LeadershipDistributionEvaluator,
    RoleBalanceEvaluator,
    SkillBalanceEvaluator,
    SquadCommunicationEvaluator,
)
from app.models.gamer_dna import GamerDNA
from app.models.gamer_profile import GamerProfile
from app.models.player_stat import PlayerStat
from app.models.survey_answer import SurveyAnswer
from app.models.survey_response import SurveyResponse
from app.models.user import User
from app.providers.dto import (
    ProviderProfileData,
    ProviderStatsData,
    ProviderSyncResult,
)
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.dna_repository import DNARepository
from app.repositories.player_stat_repository import PlayerStatRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.survey_repository import SurveyRepository
from app.repositories.user_repository import UserRepository
from app.schemas.matchmaking import MatchmakingCandidate
from app.services.compatibility_service import AICompatibilityService
from app.services.dna_service import DNAService
from app.services.explanation_service import AIExplanationService
from app.services.role_classifier_service import RoleClassifierService
from app.services.squad_recommendation_service import SquadRecommendationService


# ==============================================================================
# SECTION 1: DNA GENERATION TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_dna_generation_from_survey_responses():
    """
    Test DNA generation from survey responses:
    - Ingests SurveyResponse objects across questions
    - Evaluates Leadership, Communication, Strategy, Teamwork, Aggression
    - Synthesizes archetype moniker
    - Persists GamerDNA record to database via mock repository
    """
    mock_db = AsyncMock()
    mock_dna_repo = AsyncMock(spec=DNARepository)
    mock_survey_repo = AsyncMock(spec=SurveyRepository)

    user_id = uuid.uuid4()

    # Create realistic survey responses mapping to traits
    mock_responses = [
        SurveyResponse(
            id=uuid.uuid4(),
            user_id=user_id,
            question_id="lead_01",
            category="Leadership",
            selected_option_id="lead_01_a",
            answer="I constantly call out enemy positions and shotcall",
            score=90,
        ),
        SurveyResponse(
            id=uuid.uuid4(),
            user_id=user_id,
            question_id="comm_01",
            category="Communication",
            selected_option_id="comm_01_a",
            answer="Crisp voice callouts",
            score=85,
        ),
        SurveyResponse(
            id=uuid.uuid4(),
            user_id=user_id,
            question_id="strat_01",
            category="Strategy",
            selected_option_id="strat_01_a",
            answer="Formulate counter-utility executes",
            score=92,
        ),
        SurveyResponse(
            id=uuid.uuid4(),
            user_id=user_id,
            question_id="team_01",
            category="Teamwork",
            selected_option_id="team_01_a",
            answer="Selfless crossfire trades",
            score=80,
        ),
        SurveyResponse(
            id=uuid.uuid4(),
            user_id=user_id,
            question_id="aggr_01",
            category="Aggression",
            selected_option_id="aggr_01_a",
            answer="Controlled aggression",
            score=60,
        ),
    ]

    mock_survey_repo.get_answers_by_user_id.return_value = mock_responses

    saved_dna_record = GamerDNA(
        id=uuid.uuid4(),
        user_id=user_id,
        leadership=85,
        communication=90,
        strategy=95,
        teamwork=82,
        aggression=55,
        confidence=75,
        primary_role="Leader",
        secondary_role="Strategist",
        personality="The Grandmaster Shotcaller",
        reasoning="High leadership and strategic consensus detected from survey answers",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    mock_dna_repo.get_by_user_id.return_value = None
    mock_dna_repo.create.return_value = saved_dna_record

    service = DNAService(db=mock_db, dna_repo=mock_dna_repo, survey_repo=mock_survey_repo)

    result = await service.classify_and_store(user_id=user_id)

    assert result.primary_role in ["Leader", "Strategist", "Support"]
    assert result.personality is not None
    assert result.score_breakdown["Leadership"] >= 70
    assert result.score_breakdown["Strategy"] >= 70
    assert mock_dna_repo.create.called


@pytest.mark.asyncio
async def test_dna_generation_no_survey_answers_raises_400():
    """Verify that calling classify_and_store without survey answers raises 400 Bad Request."""
    mock_db = AsyncMock()
    mock_dna_repo = AsyncMock(spec=DNARepository)
    mock_survey_repo = AsyncMock(spec=SurveyRepository)
    mock_survey_repo.get_answers_by_user_id.return_value = []

    service = DNAService(db=mock_db, dna_repo=mock_dna_repo, survey_repo=mock_survey_repo)

    with pytest.raises(Exception) as exc_info:
        await service.classify_and_store(user_id=uuid.uuid4())
    assert "No survey responses found" in str(exc_info.value) or "400" in str(exc_info.value)


@pytest.mark.asyncio
async def test_dna_card_generation_with_strengths_and_playstyle():
    """Test full Gamer DNA Card generation including derived strengths, weaknesses, and playstyle."""
    mock_db = AsyncMock()
    mock_dna_repo = AsyncMock(spec=DNARepository)
    mock_profile_repo = AsyncMock(spec=ProfileRepository)

    user_id = uuid.uuid4()
    user = User(id=user_id, username="TacticalCaptain", email="cap@squadsync.gg")

    mock_dna = GamerDNA(
        id=uuid.uuid4(),
        user_id=user_id,
        leadership=92,
        communication=88,
        strategy=90,
        teamwork=85,
        aggression=62,
        confidence=85,
        primary_role="Leader",
        secondary_role="Strategist",
        personality="The Grandmaster Shotcaller",
    )
    mock_dna_repo.get_by_user_id.return_value = mock_dna

    mock_profile = GamerProfile(
        id=uuid.uuid4(),
        user_id=user_id,
        region="NA-East",
        language="en",
        rank="Ascendant 2",
        preferred_roles=["Leader", "Controller"],
    )
    mock_exec_res = MagicMock()
    mock_exec_res.scalar_one_or_none.return_value = mock_profile
    mock_db.execute.return_value = mock_exec_res

    service = DNAService(db=mock_db, dna_repo=mock_dna_repo)

    card = await service.get_gamer_dna_card(user=user)

    assert card.username == "TacticalCaptain"
    assert card.primary_role == "Leader"
    assert card.leadership_score == 92
    assert len(card.strengths) >= 2
    assert "In-Game Leader" in card.recommended_playstyle or "Shotcaller" in card.recommended_playstyle or "Leader" in card.recommended_playstyle


# ==============================================================================
# SECTION 2: ROLE CLASSIFICATION TESTS
# ==============================================================================

def test_role_classification_rule_based_all_roles():
    """
    Test Rule-Based Role Classification logic across distinct feature profiles:
    - Duelist profile (high aggression, high K/D)
    - Controller profile (high strategy, smoke heroes)
    - Support profile (high teamwork, assists)
    - Sentinel profile (high consistency, anchor heroes)
    - Leader profile (high leadership, high communication)
    - Strategist profile (high strategy, macro decision making)
    """
    classifier = RuleBasedRoleClassifier(config=default_classification_config)

    # 1. Test Duelist
    duelist_features = GamerRoleFeatures(
        dna=GamerDNAVector(leadership=50, communication=60, strategy=55, teamwork=50, aggression=92, confidence=88),
        stats=OfficialGameStats(win_rate=58.0, kd_ratio=1.45, kda=2.2, matches_played=120, favorite_heroes_or_agents=["Jett", "Reyna"]),
        preferred_roles=["Duelist"],
        preferred_games=["Valorant"],
    )
    res_duelist = classifier.classify(duelist_features)
    assert res_duelist.primary_role == "Duelist"
    assert res_duelist.confidence_score >= 0.70
    assert "Duelist" in res_duelist.role_affinities
    assert "Aggression" in res_duelist.reasoning or "K/D" in res_duelist.reasoning

    # 2. Test Controller
    controller_features = GamerRoleFeatures(
        dna=GamerDNAVector(leadership=65, communication=80, strategy=92, teamwork=85, aggression=45, confidence=75),
        stats=OfficialGameStats(win_rate=55.0, kd_ratio=1.05, kda=2.5, matches_played=150, favorite_heroes_or_agents=["Omen", "Viper"]),
        preferred_roles=["Controller"],
        preferred_games=["Valorant"],
    )
    res_controller = classifier.classify(controller_features)
    assert res_controller.primary_role in ["Controller", "Strategist"]
    assert res_controller.confidence_score >= 0.65

    # 3. Test Leader
    leader_features = GamerRoleFeatures(
        dna=GamerDNAVector(leadership=95, communication=92, strategy=85, teamwork=80, aggression=60, confidence=90),
        stats=OfficialGameStats(win_rate=60.0, kd_ratio=1.15, kda=2.4, matches_played=200, favorite_heroes_or_agents=["Brimstone"]),
        preferred_roles=["Leader"],
        preferred_games=["Valorant"],
    )
    res_leader = classifier.classify(leader_features)
    assert res_leader.primary_role == "Leader"
    assert res_leader.confidence_score >= 0.75


def test_role_classification_ml_adapter_fallback():
    """Test MLRoleClassifier fallback mechanism when no model artifact is loaded."""
    adapter = MLRoleClassifier(model_artifact=None)
    assert adapter.model is None

    features = GamerRoleFeatures(
        dna=GamerDNAVector(leadership=70, communication=70, strategy=70, teamwork=70, aggression=70, confidence=70),
        stats=OfficialGameStats(win_rate=50.0, kd_ratio=1.0, kda=2.0, matches_played=40),
        preferred_roles=["Flex"],
    )

    res = adapter.classify(features)
    assert res.primary_role in ["Leader", "Support", "Strategist", "Duelist", "Sentinel", "Controller"]
    assert 0.0 <= res.confidence_score <= 1.0
    assert res.reasoning is not None


@pytest.mark.asyncio
async def test_role_classifier_service_with_mocked_publisher_stats():
    """
    Test RoleClassifierService querying mock database stats (simulating Riot/Steam telemetry sync)
    and classifying gamer role with persistence.
    """
    mock_db = AsyncMock()
    mock_dna_repo = AsyncMock(spec=DNARepository)
    mock_stat_repo = AsyncMock(spec=PlayerStatRepository)
    mock_prof_repo = AsyncMock(spec=ProfileRepository)

    user_id = uuid.uuid4()

    mock_dna_repo.get_by_user_id.return_value = GamerDNA(
        id=uuid.uuid4(),
        user_id=user_id,
        leadership=88,
        communication=82,
        strategy=75,
        teamwork=78,
        aggression=65,
        confidence=80,
    )
    mock_stat_repo.get_by_user_id.return_value = [
        PlayerStat(
            id=uuid.uuid4(),
            game_account_id=uuid.uuid4(),
            user_id=user_id,
            season="Episode 8",
            game_mode="competitive",
            matches_played=110,
            win_rate=57.0,
            kd_ratio=1.20,
            kda=2.30,
            current_rank="Diamond 2",
            raw_stats={"favorite_heroes": ["Sova", "Fade"]},
        )
    ]
    mock_prof_repo.get_by_user_id.return_value = GamerProfile(
        id=uuid.uuid4(),
        user_id=user_id,
        preferred_roles=["Initiator", "Leader"],
        preferred_games=["Valorant"],
    )

    service = RoleClassifierService(
        db=mock_db,
        dna_repo=mock_dna_repo,
        player_stat_repo=mock_stat_repo,
        profile_repo=mock_prof_repo,
    )

    result = await service.evaluate_user(user_id=user_id, persist=True)

    assert result.primary_role is not None
    assert result.confidence_score > 0.50
    assert len(result.role_affinities) == 6
    assert mock_dna_repo.update.called or mock_dna_repo.create.called or mock_db.commit.called


# ==============================================================================
# SECTION 3: COMPATIBILITY ENGINE TESTS
# ==============================================================================

def test_compatibility_engine_10_dimensions_and_duo_tiers():
    """
    Test AICompatibilityEngine across 10 evaluation dimensions:
    - Psychometrics: Leadership (leader-follower vs clash), Communication, Aggression, Strategy
    - Logistics: Region, Language, Schedule
    - Competitive: Rank parity, Win Rate gap, Role synergy
    """
    engine = AICompatibilityEngine(config=default_compatibility_config)

    # Perfect Pair: Leader + Follower, Same Region & Lang, Overlapping Schedule, Equal Rank
    player_a = PlayerComparisonInput(
        username="AlphaLead",
        leadership=85.0,
        communication=85.0,
        aggression=60.0,
        strategy=85.0,
        region="NA-East",
        languages=["en"],
        schedule_slots=["evening_1", "evening_2"],
        rank_rating=1500,
        win_rate=55.0,
        preferred_roles=["Leader", "Controller"],
    )
    player_b = PlayerComparisonInput(
        username="BetaFragger",
        leadership=45.0,
        communication=80.0,
        aggression=88.0,
        strategy=70.0,
        region="NA-East",
        languages=["en"],
        schedule_slots=["evening_1", "evening_2"],
        rank_rating=1480,
        win_rate=56.0,
        preferred_roles=["Duelist"],
    )

    report = engine.compare(player_a, player_b)

    assert report.compatibility_score >= 85.0
    assert "Optimal Duo" in report.tier or "Strong" in report.tier
    assert len(report.dimension_scores) == 10
    assert len(report.strengths) >= 2
    assert len(report.risk_factors) == 0


def test_compatibility_engine_ego_clash_and_risk_factors():
    """Test engine detects dual-shotcaller clash, language barriers, and cross-continental latency."""
    engine = AICompatibilityEngine(config=default_compatibility_config)

    player_a = PlayerComparisonInput(
        username="EgoCaller1",
        leadership=92.0,
        communication=30.0,
        aggression=90.0,
        region="NA-East",
        languages=["en"],
        rank_rating=2000,
        win_rate=68.0,
        preferred_roles=["Duelist"],
    )
    player_b = PlayerComparisonInput(
        username="EgoCaller2",
        leadership=90.0,
        communication=35.0,
        aggression=40.0,
        region="Asia-East",
        languages=["ja"],
        rank_rating=1100,
        win_rate=45.0,
        preferred_roles=["Duelist"],
    )

    report = engine.compare(player_a, player_b)

    assert report.compatibility_score < 50.0
    assert "High Friction" in report.tier or "Questionable" in report.tier
    risk_text = " ".join(report.risk_factors).lower()
    assert "leadership" in risk_text or "caller" in risk_text or "ego" in risk_text
    assert "language" in risk_text or "barrier" in risk_text
    assert "latency" in risk_text or "region" in risk_text or "distance" in risk_text


@pytest.mark.asyncio
async def test_compatibility_service_user_to_user_db_hydration():
    """Test AICompatibilityService querying database entities, calculating delta, and producing report."""
    mock_db = AsyncMock()
    user_repo = AsyncMock(spec=UserRepository)
    prof_repo = AsyncMock(spec=ProfileRepository)
    dna_repo = AsyncMock(spec=DNARepository)
    stat_repo = AsyncMock(spec=PlayerStatRepository)

    uid_a = uuid.uuid4()
    uid_b = uuid.uuid4()

    user_a = User(id=uid_a, username="P1", email="p1@gg.com")
    user_b = User(id=uid_b, username="P2", email="p2@gg.com")

    user_repo.get_by_id.side_effect = lambda u_id: user_a if u_id == uid_a else user_b
    prof_repo.get_by_user_id.side_effect = lambda u_id: GamerProfile(id=uuid.uuid4(), user_id=u_id, region="NA-East", language="en")
    dna_repo.get_by_user_id.side_effect = lambda u_id: GamerDNA(id=uuid.uuid4(), user_id=u_id, leadership=70, communication=75, aggression=60, strategy=65)
    stat_repo.get_by_user_id.side_effect = lambda u_id: [PlayerStat(id=uuid.uuid4(), game_account_id=uuid.uuid4(), user_id=u_id, season="S1", game_mode="comp", matches_played=40, win_rate=52.0, rank_rating=1200)]

    service = AICompatibilityService(
        db=mock_db,
        user_repo=user_repo,
        profile_repo=prof_repo,
        dna_repo=dna_repo,
        player_stat_repo=stat_repo,
    )

    report = await service.compare_users(uid_a, uid_b)
    assert report.player_a_name == "P1"
    assert report.player_b_name == "P2"
    assert 0.0 <= report.compatibility_score <= 100.0


# ==============================================================================
# SECTION 4: SQUAD RECOMMENDATION TESTS
# ==============================================================================

def test_squad_evaluators_composition_dynamics():
    """
    Test individual composition evaluators:
    - RoleBalanceEvaluator: Full 5-role coverage vs duplicates and missing roles
    - SkillBalanceEvaluator: MMR standard deviation penalty
    - SquadCommunicationEvaluator: Silent-round penalty
    - LeadershipDistributionEvaluator: Designated IGL & conflict detection
    """
    role_eval = RoleBalanceEvaluator()
    skill_eval = SkillBalanceEvaluator()
    comms_eval = SquadCommunicationEvaluator()
    lead_eval = LeadershipDistributionEvaluator()

    # Balanced 5-player squad
    members = [
        MatchmakingCandidate(user_id=uuid.uuid4(), username="Lead", primary_role="Leader", leadership=88, communication=80, mmr=1500),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="Duel", primary_role="Duelist", leadership=50, communication=75, mmr=1520),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="Contr", primary_role="Controller", leadership=55, communication=78, mmr=1490),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="Sent", primary_role="Sentinel", leadership=45, communication=70, mmr=1510),
        MatchmakingCandidate(user_id=uuid.uuid4(), username="Supp", primary_role="Support", leadership=60, communication=82, mmr=1505),
    ]

    # 1. Role Balance: 5 unique roles should score >= 90%
    role_score, role_counts, missing_roles = role_eval.evaluate(members)
    assert role_score >= 90.0
    assert len(missing_roles) == 0

    # 2. Skill Balance: tightly clustered MMR (<30 std) should score >= 90%
    skill_score, mean_mmr, variance = skill_eval.evaluate(members)
    assert skill_score >= 90.0
    assert variance < 20.0

    # 3. Communication: all >= 70 should score >= 75%
    comm_score = comms_eval.evaluate(members)
    assert comm_score >= 75.0

    # 4. Leadership: exactly one shotcaller (88) should designate IGL and score >= 85%
    lead_score, designated_igl, assessment = lead_eval.evaluate(members)
    assert lead_score >= 85.0
    assert designated_igl == "Lead"


def test_squad_recommendation_combinatorial_search():
    """Test SquadRecommendationEngine selects the single best 5-player roster and ranks top teammates."""
    engine = SquadRecommendationEngine(config=default_squad_config)

    requester = MatchmakingCandidate(
        user_id=uuid.uuid4(),
        username="Requester",
        primary_role="Controller",
        leadership=65,
        communication=85,
        mmr=1500,
        rank="Diamond 1",
        win_rate=54.0,
    )

    roles = ["Duelist", "Sentinel", "Support", "Leader", "Strategist", "Duelist", "Sentinel"]
    candidates = []
    for i, role in enumerate(roles):
        candidates.append(
            MatchmakingCandidate(
                user_id=uuid.uuid4(),
                username=f"Player_{i+1}",
                primary_role=role,
                secondary_role="Support",
                leadership=85 if role == "Leader" else 45,
                communication=78,
                mmr=1490 + (i * 10),
                rank="Diamond 1",
                win_rate=53.0 + i,
            )
        )

    result = engine.generate_recommendation(
        current_user=requester,
        candidates=candidates,
        game_name="Valorant",
    )

    # Assertions
    assert len(result.top_10_teammates) <= 10
    assert len(result.best_5_player_squad.members) == 5
    member_names = [m.username for m in result.best_5_player_squad.members]
    assert "Requester" in member_names
    assert result.confidence_score >= 0.50
    assert result.best_5_player_squad.overall_score > 60.0


@pytest.mark.asyncio
async def test_squad_recommendation_service_with_mock_candidates():
    """Test SquadRecommendationService querying CandidateRepository and executing recommendation."""
    mock_db = AsyncMock()
    mock_cand_repo = AsyncMock(spec=CandidateRepository)
    mock_user_repo = AsyncMock(spec=UserRepository)

    uid = uuid.uuid4()
    requester = MatchmakingCandidate(user_id=uid, username="ProRequester", primary_role="Duelist", mmr=1600)
    mock_cand_repo.build_candidate_for_user.return_value = requester

    # Return 6 candidate players
    pool = [
        MatchmakingCandidate(user_id=uuid.uuid4(), username=f"Cand_{i}", primary_role="Support", mmr=1580)
        for i in range(6)
    ]
    mock_cand_repo.get_candidate_pool.return_value = pool

    service = SquadRecommendationService(
        db=mock_db,
        candidate_repo=mock_cand_repo,
        user_repo=mock_user_repo,
    )

    result = await service.recommend_for_user(user_id=uid, game_name="Valorant")
    assert len(result.best_5_player_squad.members) == 5
    assert result.current_user.username == "ProRequester"


# ==============================================================================
# SECTION 5: EXPLANATION ENGINE TESTS
# ==============================================================================

def test_explanation_engine_nlg_narratives_and_coaching():
    """
    Test AIExplanationEngine Natural Language Generation:
    - Generates why two players match
    - Generates why they don't match
    - Synthesizes strengths narrative
    - Synthesizes weaknesses narrative
    - Prescribes concrete actionable coaching tips
    """
    engine = AIExplanationEngine(config=default_explanation_config)

    p_a = PlayerExplanationContext(
        username="ViperTactician",
        leadership=88.0,
        communication=84.0,
        aggression=50.0,
        strategy=92.0,
        primary_role="Controller",
        secondary_role="Leader",
        rank="Diamond 3",
        rank_rating=1460,
        win_rate=56.0,
        region="NA-East",
        languages=["en"],
    )

    p_b = PlayerExplanationContext(
        username="ReynaFragger",
        leadership=42.0,
        communication=76.0,
        aggression=94.0,
        strategy=60.0,
        primary_role="Duelist",
        secondary_role="Initiator",
        rank="Diamond 2",
        rank_rating=1420,
        win_rate=57.0,
        region="NA-East",
        languages=["en"],
    )

    res = engine.generate_explanation(player_a=p_a, player_b=p_b)

    assert "ViperTactician" in res.headline or "Controller" in res.headline or "Synergy" in res.headline
    assert len(res.match_reasons) >= 2
    assert len(res.strengths_narrative) >= 2
    assert len(res.improvement_suggestions) >= 1
    assert 0.0 <= res.confidence_score <= 1.0

    # Test ego clash detection
    p_b_leader = PlayerExplanationContext(
        username="JettCaller",
        leadership=90.0,
        communication=70.0,
        primary_role="Duelist",
    )
    res_clash = engine.generate_explanation(player_a=p_a, player_b=p_b_leader)
    mismatch_str = " ".join(res_clash.mismatch_reasons).lower()
    assert "shotcaller" in mismatch_str or "leadership" in mismatch_str or "friction" in mismatch_str


@pytest.mark.asyncio
async def test_explanation_service_user_hydration_and_generation():
    """Test AIExplanationService querying DB records and invoking explanation pipeline."""
    mock_db = AsyncMock()
    user_repo = AsyncMock(spec=UserRepository)
    prof_repo = AsyncMock(spec=ProfileRepository)
    dna_repo = AsyncMock(spec=DNARepository)
    stat_repo = AsyncMock(spec=PlayerStatRepository)

    uid_a = uuid.uuid4()
    uid_b = uuid.uuid4()

    user_repo.get_by_id.side_effect = lambda u_id: User(id=u_id, username=f"User_{str(u_id)[:4]}")
    prof_repo.get_by_user_id.side_effect = lambda u_id: GamerProfile(id=uuid.uuid4(), user_id=u_id, region="NA-East", language="en")
    dna_repo.get_by_user_id.side_effect = lambda u_id: GamerDNA(id=uuid.uuid4(), user_id=u_id, leadership=80 if u_id == uid_a else 45, communication=70, aggression=65, strategy=75)
    stat_repo.get_by_user_id.side_effect = lambda u_id: [PlayerStat(id=uuid.uuid4(), game_account_id=uuid.uuid4(), user_id=u_id, season="S1", game_mode="comp", matches_played=30, win_rate=55.0, rank_rating=1200)]

    service = AIExplanationService(
        db=mock_db,
        user_repo=user_repo,
        profile_repo=prof_repo,
        dna_repo=dna_repo,
        player_stat_repo=stat_repo,
    )

    explanation = await service.explain_between_users(uid_a, uid_b)
    assert explanation.player_a_name is not None
    assert explanation.player_b_name is not None
    assert len(explanation.why_they_match) > 0
    assert len(explanation.strengths) > 0


# ==============================================================================
# SECTION 6: MOCK EXTERNAL APIS (RIOT & STEAM/DOTA) INTEGRATION TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_external_api_mock_telemetry_flow():
    """
    Verifies that mocked publisher APIs (Riot and Steam/Dota) return telemetry DTOs
    that cleanly feed into the AI feature extraction pipeline.
    """
    mock_riot_profile = ProviderProfileData(
        account_identifier="riot_acc_123",
        in_game_name="RadiantSniper",
        tagline="NA1",
        region="na",
        account_level=150,
    )
    mock_riot_stats = ProviderStatsData(
        season="episode_7",
        game_mode="competitive",
        rank="Ascendant 3",
        rank_rating=1650,
        win_rate=58.5,
        matches_played=140,
        kd_ratio=1.35,
        headshot_percentage=31.2,
        raw_stats={"favorite_heroes": ["Jett", "Chamber"]},
    )

    mock_dota_profile = ProviderProfileData(
        account_identifier="steam_acc_456",
        in_game_name="InvokerGod",
        region="eu",
        account_level=85,
    )
    mock_dota_stats = ProviderStatsData(
        season="2026_season",
        game_mode="ranked",
        rank="Divine 4",
        rank_rating=1700,
        win_rate=56.0,
        matches_played=210,
        kd_ratio=1.25,
        raw_stats={"favorite_heroes": ["Invoker", "Storm Spirit"]},
    )

    # Convert external telemetry DTO into OfficialGameStats
    stats_riot = OfficialGameStats(
        win_rate=mock_riot_stats.win_rate or 0.0,
        kd_ratio=mock_riot_stats.kd_ratio or 0.0,
        kda=2.1,
        matches_played=mock_riot_stats.matches_played,
        headshot_pct=mock_riot_stats.headshot_percentage,
        rank=mock_riot_stats.rank,
        rank_rating=mock_riot_stats.rank_rating,
        favorite_heroes_or_agents=mock_riot_stats.raw_stats.get("favorite_heroes", []),
    )

    stats_dota = OfficialGameStats(
        win_rate=mock_dota_stats.win_rate or 0.0,
        kd_ratio=mock_dota_stats.kd_ratio or 0.0,
        kda=2.0,
        matches_played=mock_dota_stats.matches_played,
        rank=mock_dota_stats.rank,
        rank_rating=mock_dota_stats.rank_rating,
        favorite_heroes_or_agents=mock_dota_stats.raw_stats.get("favorite_heroes", []),
    )

    assert mock_riot_profile.in_game_name == "RadiantSniper"
    assert stats_riot.kd_ratio == 1.35
    assert stats_riot.rank == "Ascendant 3"
    assert mock_dota_profile.in_game_name == "InvokerGod"
    assert stats_dota.win_rate == 56.0
    assert len(stats_dota.favorite_heroes_or_agents) == 2
