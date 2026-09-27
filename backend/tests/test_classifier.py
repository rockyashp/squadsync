"""
Unit tests for rule-based Gamer Role Classification engine and all 6 tactical roles:
Leader, Support, Strategist, Duelist, Sentinel, Controller.
"""

import uuid
import pytest

from app.models.survey_response import SurveyResponse
from app.services.classifier import (
    ControllerRule,
    DuelistRule,
    LeaderRule,
    RoleClassifierEngine,
    SentinelRule,
    StrategistRule,
    SupportRule,
    classifier_engine,
)


def test_leader_rule_evaluation():
    """Test Leader affinity and reasoning generation."""
    rule = LeaderRule()
    assert rule.name == "Leader"

    scores = {"Leadership": 90, "Communication": 80, "Strategy": 70, "Teamwork": 60, "Aggression": 50}
    # 0.50*90 + 0.30*80 + 0.20*70 = 45 + 24 + 14 = 83.0
    affinity = rule.calculate_affinity(scores)
    assert affinity == 83.0
    reasoning = rule.get_reasoning(scores)
    assert "90/100" in reasoning
    assert "80/100" in reasoning


def test_support_rule_evaluation():
    """Test Support affinity prioritizing teamwork, comms, and controlled aggression."""
    rule = SupportRule()
    assert rule.name == "Support"

    scores = {"Leadership": 50, "Communication": 85, "Strategy": 60, "Teamwork": 95, "Aggression": 20}
    # 0.50*95 + 0.30*85 + 0.20*(100-20) = 47.5 + 25.5 + 16.0 = 89.0
    affinity = rule.calculate_affinity(scores)
    assert affinity == 89.0
    reasoning = rule.get_reasoning(scores)
    assert "95/100" in reasoning


def test_strategist_rule_evaluation():
    """Test Strategist affinity prioritizing macro planning and counter-play."""
    rule = StrategistRule()
    assert rule.name == "Strategist"

    scores = {"Leadership": 70, "Communication": 70, "Strategy": 95, "Teamwork": 60, "Aggression": 40}
    # 0.50*95 + 0.25*70 + 0.25*70 = 47.5 + 17.5 + 17.5 = 82.5
    affinity = rule.calculate_affinity(scores)
    assert affinity == 82.5
    reasoning = rule.get_reasoning(scores)
    assert "95/100" in reasoning


def test_duelist_rule_evaluation():
    """Test Duelist affinity prioritizing aggression and entry tempo."""
    rule = DuelistRule()
    assert rule.name == "Duelist"

    scores = {"Leadership": 60, "Communication": 50, "Strategy": 40, "Teamwork": 40, "Aggression": 95}
    # 0.60*95 + 0.25*60 + 0.15*40 = 57.0 + 15.0 + 6.0 = 78.0
    affinity = rule.calculate_affinity(scores)
    assert affinity == 78.0
    reasoning = rule.get_reasoning(scores)
    assert "95/100" in reasoning


def test_sentinel_rule_evaluation():
    """Test Sentinel affinity prioritizing defense, perimeter security, and anchor patience."""
    rule = SentinelRule()
    assert rule.name == "Sentinel"

    scores = {"Leadership": 40, "Communication": 60, "Strategy": 85, "Teamwork": 80, "Aggression": 25}
    # 0.40*85 + 0.35*80 + 0.25*(100-25) = 34.0 + 28.0 + 18.75 = 80.75
    affinity = rule.calculate_affinity(scores)
    assert affinity == 80.75
    reasoning = rule.get_reasoning(scores)
    assert "85/100" in reasoning


def test_controller_rule_evaluation():
    """Test Controller affinity prioritizing smoke geometry, teamwork, and crossfires."""
    rule = ControllerRule()
    assert rule.name == "Controller"

    scores = {"Leadership": 50, "Communication": 75, "Strategy": 90, "Teamwork": 85, "Aggression": 45}
    # 0.40*90 + 0.40*85 + 0.20*75 = 36.0 + 34.0 + 15.0 = 85.0
    affinity = rule.calculate_affinity(scores)
    assert affinity == 85.0
    reasoning = rule.get_reasoning(scores)
    assert "90/100" in reasoning


def test_category_scores_calculation():
    """Test calculation of dimension averages from survey response instances."""
    engine = RoleClassifierEngine()
    uid = uuid.uuid4()

    sample_responses = [
        SurveyResponse(user_id=uid, question_id="lead_01", category="Leadership", answer="A", score=100),
        SurveyResponse(user_id=uid, question_id="lead_02", category="Leadership", answer="B", score=80),
        SurveyResponse(user_id=uid, question_id="comm_01", category="Communication", answer="A", score=90),
        SurveyResponse(user_id=uid, question_id="strat_01", category="Strategy", answer="A", score=75),
        SurveyResponse(user_id=uid, question_id="team_01", category="Teamwork", answer="A", score=85),
        SurveyResponse(user_id=uid, question_id="aggr_01", category="Aggression", answer="A", score=70),
    ]

    scores = engine.calculate_category_scores(sample_responses)
    assert scores["Leadership"] == 90  # (100 + 80) / 2
    assert scores["Communication"] == 90
    assert scores["Strategy"] == 75
    assert scores["Teamwork"] == 85
    assert scores["Aggression"] == 70


def test_full_classification_pipeline():
    """Test end-to-end classification generating primary, secondary, reasoning, and personality."""
    uid = uuid.uuid4()
    # Create responses tailored for Duelist + Leader
    responses = [
        SurveyResponse(user_id=uid, question_id="aggr_01", category="Aggression", answer="A", score=100),
        SurveyResponse(user_id=uid, question_id="aggr_02", category="Aggression", answer="A", score=100),
        SurveyResponse(user_id=uid, question_id="lead_01", category="Leadership", answer="A", score=85),
        SurveyResponse(user_id=uid, question_id="strat_01", category="Strategy", answer="B", score=50),
        SurveyResponse(user_id=uid, question_id="comm_01", category="Communication", answer="C", score=50),
        SurveyResponse(user_id=uid, question_id="team_01", category="Teamwork", answer="C", score=40),
    ]

    result = classifier_engine.classify(responses)

    assert result.primary_role == "Duelist"
    assert result.secondary_role == "Leader"
    assert "The Aggressive Warlord" in result.personality or "Duelist" in result.personality
    assert "Primary: Duelist" in result.reasoning
    assert "Secondary: Leader" in result.reasoning
    assert len(result.role_affinities) == 6
    assert all(role in result.role_affinities for role in ["Leader", "Support", "Strategist", "Duelist", "Sentinel", "Controller"])
