"""
Unit and integration tests for the Gamer Role Classification Engine.
Tests all 6 role rules, multi-signal feature extraction, confidence scoring,
explainable reasoning, ML adapter swappability, service orchestration, and FastAPI endpoints.
"""

from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.role_classifier import (
    BaseRoleClassifier,
    GamerDNAVector,
    GamerRoleFeatures,
    MLRoleClassifier,
    OfficialGameStats,
    RoleClassificationConfig,
    RoleClassificationResult,
    RuleBasedRoleClassifier,
    default_classification_config,
)
from app.core.role_classifier.rules import (
    ControllerRule,
    DuelistRule,
    LeaderRule,
    SentinelRule,
    StrategistRule,
    SupportRule,
)
from app.main import app
from app.models.gamer_dna import GamerDNA
from app.models.gamer_profile import GamerProfile
from app.models.player_stat import PlayerStat
from app.models.user import User
from app.schemas.role_classifier import (
    GamerDNAInput,
    OfficialGameStatsInput,
    RoleClassifierEvaluateRequest,
)
from app.services.role_classifier_service import RoleClassifierService


# ------------------------------------------------------------------------------
# Feature Vector & Normalization Tests
# ------------------------------------------------------------------------------

def test_gamer_dna_vector_normalization():
    """Test DNA vector bounded normalization to [0.0, 1.0]."""
    dna = GamerDNAVector(
        leadership=90.0,
        communication=80.0,
        strategy=70.0,
        teamwork=60.0,
        aggression=50.0,
        confidence=100.0,
    )
    nd = dna.to_normalized_dict()
    assert nd["leadership"] == 0.90
    assert nd["communication"] == 0.80
    assert nd["confidence"] == 1.0
    assert len(dna.to_list()) == 6


def test_official_game_stats_normalization():
    """Test in-game statistics normalization against benchmarks."""
    stats = OfficialGameStats(
        win_rate=58.0,
        kd_ratio=1.5,
        kda=3.0,
        matches_played=100,
        headshot_pct=25.0,
    )
    norms = stats.normalize()
    assert 0.0 <= norms["kd_norm"] <= 1.0
    assert 0.0 <= norms["win_rate_norm"] <= 1.0
    assert 0.0 <= norms["kda_norm"] <= 1.0
    assert 0.0 <= norms["headshot_norm"] <= 1.0
    assert norms["sample_factor"] == 1.0


def test_gamer_role_features_dense_vector():
    """Test 14-dimensional dense vector generation for ML models."""
    features = GamerRoleFeatures(
        dna=GamerDNAVector(leadership=85.0, aggression=90.0),
        stats=OfficialGameStats(win_rate=55.0, kd_ratio=1.4, matches_played=75),
        preferred_roles=["Duelist", "Leader"],
        preferred_games=["Valorant", "Dota 2"],
    )
    dense = features.to_dense_vector()
    assert len(dense) == 14
    for val in dense:
        assert isinstance(val, float)
        assert 0.0 <= val <= 1.0

    feat_dict = features.to_feature_dict()
    assert "dna_leadership" in feat_dict
    assert "stats_kd_norm" in feat_dict
    assert feat_dict["preferred_roles_count"] == 2.0


# ------------------------------------------------------------------------------
# Individual Role Rule Evaluation Tests
# ------------------------------------------------------------------------------

def test_duelist_rule_evaluation():
    """Test Duelist rule rewards high aggression, confidence, KD, and entry preferences."""
    rule = DuelistRule()
    features = GamerRoleFeatures(
        dna=GamerDNAVector(aggression=92.0, confidence=88.0, leadership=70.0),
        stats=OfficialGameStats(
            kd_ratio=1.65,
            headshot_pct=32.0,
            win_rate=58.0,
            favorite_heroes_or_agents=["Jett", "Reyna"],
        ),
        preferred_roles=["Duelist"],
        preferred_games=["Valorant"],
    )
    eval_result = rule.evaluate(features, default_classification_config)
    assert eval_result.role_name == "Duelist"
    assert eval_result.affinity_score > 75.0
    assert eval_result.dna_score > 80.0
    assert eval_result.preference_score == 100.0
    assert "Duelist" in eval_result.reasoning_snippet or "aggression" in eval_result.reasoning_snippet


def test_leader_rule_evaluation():
    """Test Leader rule rewards commanding comms, leadership, and high win rate."""
    rule = LeaderRule()
    features = GamerRoleFeatures(
        dna=GamerDNAVector(leadership=95.0, communication=90.0, confidence=85.0),
        stats=OfficialGameStats(win_rate=62.0, kd_ratio=1.1, matches_played=80),
        preferred_roles=["IGL", "Leader"],
        preferred_games=["Valorant"],
    )
    eval_result = rule.evaluate(features, default_classification_config)
    assert eval_result.role_name == "Leader"
    assert eval_result.affinity_score > 75.0
    assert eval_result.dna_score > 85.0
    assert eval_result.preference_score == 100.0


def test_support_rule_evaluation():
    """Test Support rule rewards teamwork, high assists (KDA), and low aggression."""
    rule = SupportRule()
    features = GamerRoleFeatures(
        dna=GamerDNAVector(teamwork=95.0, communication=88.0, aggression=20.0),
        stats=OfficialGameStats(kd_ratio=0.85, kda=3.5, win_rate=54.0),
        preferred_roles=["Support", "Healer"],
        preferred_games=["Dota 2"],
    )
    eval_result = rule.evaluate(features, default_classification_config)
    assert eval_result.role_name == "Support"
    assert eval_result.affinity_score > 70.0
    assert "teamwork" in eval_result.reasoning_snippet.lower()


def test_strategist_rule_evaluation():
    """Test Strategist rule rewards deep strategy and macro round conversion."""
    rule = StrategistRule()
    features = GamerRoleFeatures(
        dna=GamerDNAVector(strategy=94.0, leadership=75.0, communication=72.0),
        stats=OfficialGameStats(win_rate=60.0, kd_ratio=1.15, kda=2.5),
        preferred_roles=["Strategist"],
        preferred_games=["Valorant"],
    )
    eval_result = rule.evaluate(features, default_classification_config)
    assert eval_result.role_name == "Strategist"
    assert eval_result.affinity_score > 70.0


def test_sentinel_rule_evaluation():
    """Test Sentinel rule rewards patient defense, site anchoring, and solid KD."""
    rule = SentinelRule()
    features = GamerRoleFeatures(
        dna=GamerDNAVector(strategy=88.0, teamwork=85.0, aggression=25.0),
        stats=OfficialGameStats(kd_ratio=1.2, kda=2.8, win_rate=55.0),
        preferred_roles=["Sentinel", "Anchor"],
        preferred_games=["Valorant"],
    )
    eval_result = rule.evaluate(features, default_classification_config)
    assert eval_result.role_name == "Sentinel"
    assert eval_result.affinity_score > 70.0


def test_controller_rule_evaluation():
    """Test Controller rule rewards vision denial, spatial utility, and teamwork."""
    rule = ControllerRule()
    features = GamerRoleFeatures(
        dna=GamerDNAVector(strategy=85.0, teamwork=85.0, communication=80.0),
        stats=OfficialGameStats(kd_ratio=1.05, kda=2.9, win_rate=56.0),
        preferred_roles=["Controller", "Smoker"],
        preferred_games=["Valorant"],
    )
    eval_result = rule.evaluate(features, default_classification_config)
    assert eval_result.role_name == "Controller"
    assert eval_result.affinity_score > 70.0


# ------------------------------------------------------------------------------
# Engine Classification, Confidence & Explainability Tests
# ------------------------------------------------------------------------------

def test_engine_primary_secondary_classification():
    """Test full engine produces primary role, secondary role, confidence score, and reasoning."""
    engine = RuleBasedRoleClassifier()
    features = GamerRoleFeatures(
        dna=GamerDNAVector(
            leadership=85.0,
            communication=82.0,
            strategy=70.0,
            aggression=90.0,
            confidence=85.0,
            teamwork=55.0,
        ),
        stats=OfficialGameStats(
            kd_ratio=1.45,
            headshot_pct=30.0,
            win_rate=57.0,
            matches_played=120,
            favorite_heroes_or_agents=["Jett"],
        ),
        preferred_roles=["Duelist"],
        preferred_games=["Valorant"],
    )

    result = engine.classify(features)

    assert result.primary_role == "Duelist"
    assert result.secondary_role in ["Leader", "Strategist"]
    assert 0.0 <= result.confidence_score <= 1.0
    assert result.confidence_score > 0.65  # Strong alignment yields high confidence
    assert "PRIMARY ROLE: Duelist" in result.reasoning
    assert "SECONDARY ROLE:" in result.reasoning
    assert result.personality is not None
    assert len(result.role_affinities) == 6
    assert "gamer_dna_influence" in result.feature_importance


def test_engine_low_match_sample_confidence_penalty():
    """Test confidence is dampened when player has very few recorded matches."""
    engine = RuleBasedRoleClassifier()

    # Features with 5 matches (below minimum 10 floor)
    low_sample = GamerRoleFeatures(
        dna=GamerDNAVector(aggression=90.0),
        stats=OfficialGameStats(matches_played=3),
    )
    # Features with 100 matches
    high_sample = GamerRoleFeatures(
        dna=GamerDNAVector(aggression=90.0),
        stats=OfficialGameStats(matches_played=100),
    )

    low_res = engine.classify(low_sample)
    high_res = engine.classify(high_sample)

    assert low_res.confidence_score < high_res.confidence_score


# ------------------------------------------------------------------------------
# ML Adapter Swappability Tests
# ------------------------------------------------------------------------------

def test_ml_classifier_fallback_to_rules():
    """Test MLRoleClassifier transparently falls back to rule engine if no weights artifact."""
    ml_clf = MLRoleClassifier(model_artifact=None)
    features = GamerRoleFeatures(dna=GamerDNAVector(aggression=95.0, confidence=90.0))
    result = ml_clf.classify(features)
    assert result.primary_role == "Duelist"
    assert result.confidence_score > 0.50


def test_ml_classifier_custom_model_prediction():
    """Test MLRoleClassifier consumes mock ML model returning probability distribution."""
    # Mock model predict_proba returning 6 class probabilities
    mock_model = MagicMock()
    mock_model.predict_proba.return_value = [[0.10, 0.65, 0.05, 0.10, 0.05, 0.05]]

    ml_clf = MLRoleClassifier(model_artifact=mock_model)
    features = GamerRoleFeatures()
    result = ml_clf.classify(features)

    # Class at index 1 is "Support" in default roles
    assert result.primary_role == "Support"
    assert result.confidence_score > 0.70
    assert "ML confidence" in result.reasoning


# ------------------------------------------------------------------------------
# RoleClassifierService Unit Tests
# ------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_role_classifier_service_evaluate_payload():
    """Test service evaluates directly from request payload."""
    mock_db = AsyncMock()
    service = RoleClassifierService(db=mock_db)

    req = RoleClassifierEvaluateRequest(
        gamer_dna=GamerDNAInput(leadership=90.0, communication=85.0),
        official_stats=OfficialGameStatsInput(win_rate=60.0, kd_ratio=1.2, matches_played=80),
        preferred_roles=["Leader"],
        preferred_games=["Valorant"],
    )

    result = service.evaluate_payload(req)
    assert result.primary_role == "Leader"
    assert result.confidence_score > 0.60


@pytest.mark.asyncio
async def test_role_classifier_service_evaluate_user_hydrates_db():
    """Test service fetches user's stored DNA, player stats, and profile to classify and persist."""
    user_id = uuid.uuid4()
    mock_db = AsyncMock()
    mock_dna_repo = AsyncMock()
    mock_stat_repo = AsyncMock()
    mock_profile_repo = AsyncMock()

    # Mock stored records
    mock_dna_repo.get_by_user_id.return_value = GamerDNA(
        id=uuid.uuid4(),
        user_id=user_id,
        leadership=85,
        communication=80,
        strategy=65,
        teamwork=60,
        aggression=90,
        confidence=85,
        primary_role="Duelist",
        personality="The Fearless Vanguard",
    )
    mock_stat_repo.get_by_user_id.return_value = [
        PlayerStat(
            id=uuid.uuid4(),
            user_id=user_id,
            game_account_id=uuid.uuid4(),
            season="S1",
            game_mode="competitive",
            matches_played=50,
            win_rate=56.0,
            kd_ratio=1.35,
            kda=2.1,
            headshot_pct=25.0,
            raw_stats={"preferred_agent": "Jett"},
        )
    ]
    mock_profile_repo.get_by_user_id.return_value = GamerProfile(
        id=uuid.uuid4(),
        user_id=user_id,
        preferred_roles=["Duelist"],
        preferred_games=["Valorant"],
    )

    service = RoleClassifierService(
        db=mock_db,
        dna_repo=mock_dna_repo,
        player_stat_repo=mock_stat_repo,
        profile_repo=mock_profile_repo,
    )

    result = await service.evaluate_user(user_id=user_id, persist=True)
    assert result.primary_role == "Duelist"
    assert mock_dna_repo.update.called


# ------------------------------------------------------------------------------
# FastAPI HTTP Endpoint Tests
# ------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_evaluate_endpoint_http():
    """Test POST /api/v1/classifier/evaluate endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "gamer_dna": {
                "leadership": 88.0,
                "communication": 82.0,
                "strategy": 70.0,
                "aggression": 60.0,
                "teamwork": 65.0,
                "confidence": 80.0,
            },
            "official_stats": {
                "win_rate": 59.0,
                "kd_ratio": 1.15,
                "kda": 2.2,
                "matches_played": 90,
                "headshot_pct": 22.0,
            },
            "preferred_roles": ["Leader"],
            "preferred_games": ["Valorant"],
        }
        res = await client.post("/api/v1/classifier/evaluate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["primary_role"] == "Leader"
        assert "confidence_score" in data["data"]
        assert "reasoning" in data["data"]
        assert "personality" in data["data"]
        assert "role_affinities" in data["data"]


@pytest.mark.asyncio
async def test_get_classifier_config_endpoint_http():
    """Test GET /api/v1/classifier/config endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/classifier/config")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert "supported_roles" in data["data"]
        assert "Leader" in data["data"]["supported_roles"]
        assert "signal_weights" in data["data"]


@pytest.mark.asyncio
async def test_classify_me_unauthenticated(client: AsyncClient):
    """Test POST /api/v1/classifier/me requires authentication (401 Unauthorized)."""
    response = await client.post("/api/v1/classifier/me")
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False


@pytest.mark.asyncio
async def test_classify_me_authenticated(authenticated_client: AsyncClient):
    """Test POST /api/v1/classifier/me executes classification for authenticated user."""
    response = await authenticated_client.post("/api/v1/classifier/me")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "primary_role" in data["data"]
    assert "secondary_role" in data["data"]
    assert "confidence_score" in data["data"]
    assert "reasoning" in data["data"]
    assert "personality" in data["data"]
