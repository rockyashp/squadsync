"""
Tests for Gamer DNA Survey module:
- 20 Behavioral questions retrieval across 6 categories
- Verification that scoring weights are hidden from public and client responses
- Survey submission validation and separate answer storage
- Survey history retrieval
- Endpoints: GET /survey/questions, POST /survey, GET /survey/history
"""

import pytest
from httpx import AsyncClient

from app.core.survey_data import SURVEY_QUESTION_BANK, get_all_questions_public


def test_question_bank_structure():
    """Verify internal question bank contains exactly 20 questions across 6 categories."""
    assert len(SURVEY_QUESTION_BANK) == 20

    expected_categories = {
        "Leadership": 4,
        "Communication": 3,
        "Strategy": 3,
        "Aggression": 3,
        "Teamwork": 3,
        "Confidence": 4,
    }

    for cat, expected_count in expected_categories.items():
        cat_questions = [q for q in SURVEY_QUESTION_BANK if q["category"] == cat]
        assert len(cat_questions) == expected_count, f"Category '{cat}' must have exactly {expected_count} questions."
        for q in cat_questions:
            assert len(q["options"]) == 4, f"Question '{q['id']}' must have 4 multiple-choice options."
            for opt in q["options"]:
                assert "score" in opt, f"Internal option '{opt['id']}' must have a scoring weight."


def test_public_questions_strip_weights():
    """Verify get_all_questions_public() strictly removes scoring weights from client payloads."""
    public_questions = get_all_questions_public()
    assert len(public_questions) == 20

    for q in public_questions:
        assert "score" not in q
        for opt in q["options"]:
            assert "score" not in opt, "Scoring weight was leaked in public options!"
            assert "id" in opt
            assert "text" in opt


@pytest.mark.asyncio
async def test_get_survey_questions_api(client: AsyncClient):
    """Test GET /api/v1/survey/questions and GET /survey/questions endpoints return 20 questions without scoring weights."""
    for url in ["/api/v1/survey/questions", "/survey/questions"]:
        response = await client.get(url)
        assert response.status_code == 200

        payload = response.json()
        assert payload["success"] is True
        assert "data" in payload
        assert len(payload["data"]) == 20

        # Confirm weights are strictly hidden over the wire
        for q in payload["data"]:
            assert "score" not in q
            assert "category" in q
            assert "options" in q
            for opt in q["options"]:
                assert "score" not in opt


@pytest.mark.asyncio
async def test_submit_survey_unauthenticated(client: AsyncClient):
    """Test POST /survey and POST /api/v1/survey require authentication."""
    body = {
        "answers": [
            {"question_id": "lead_01", "selected_option_id": "lead_01_a"}
        ]
    }
    for url in ["/survey", "/api/v1/survey", "/api/v1/survey/submit"]:
        response = await client.post(url, json=body)
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert any(
            word in data["message"].lower()
            for word in ["token", "credentials", "authenticated", "not authenticated"]
        )


@pytest.mark.asyncio
async def test_submit_survey_invalid_question_id(authenticated_client: AsyncClient):
    """Test POST /api/v1/survey with non-existent question returns 400 Bad Request."""
    body = {
        "answers": [
            {"question_id": "invalid_q_id_999", "selected_option_id": "lead_01_a"}
        ]
    }
    response = await authenticated_client.post("/api/v1/survey", json=body)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "invalid_q_id_999" in data["message"]


@pytest.mark.asyncio
async def test_submit_survey_invalid_option_id(authenticated_client: AsyncClient):
    """Test POST /api/v1/survey with option belonging to a different question returns 400."""
    body = {
        "answers": [
            {"question_id": "lead_01", "selected_option_id": "comm_01_a"}  # Mismatched option
        ]
    }
    response = await authenticated_client.post("/api/v1/survey", json=body)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "invalid for question" in data["message"]


@pytest.mark.asyncio
async def test_submit_full_survey_and_separate_answer_storage(authenticated_client: AsyncClient):
    """
    Test submitting all 20 questions via POST /survey:
    - Verifies all 6 category scores are calculated server-side
    - Confirms individual answer records are created separately
    - Tests GET /survey/history retrieval without leaking question scoring weights
    """
    # Build complete 20-answer submission payload
    answers_payload = [
        {"question_id": "lead_01", "selected_option_id": "lead_01_a"},
        {"question_id": "lead_02", "selected_option_id": "lead_02_a"},
        {"question_id": "lead_03", "selected_option_id": "lead_03_a"},
        {"question_id": "lead_04", "selected_option_id": "lead_04_a"},
        {"question_id": "comm_01", "selected_option_id": "comm_01_a"},
        {"question_id": "comm_02", "selected_option_id": "comm_02_a"},
        {"question_id": "comm_03", "selected_option_id": "comm_03_a"},
        {"question_id": "strat_01", "selected_option_id": "strat_01_a"},
        {"question_id": "strat_02", "selected_option_id": "strat_02_a"},
        {"question_id": "strat_03", "selected_option_id": "strat_03_a"},
        {"question_id": "aggr_01", "selected_option_id": "aggr_01_a"},
        {"question_id": "aggr_02", "selected_option_id": "aggr_02_a"},
        {"question_id": "aggr_03", "selected_option_id": "aggr_03_a"},
        {"question_id": "team_01", "selected_option_id": "team_01_a"},
        {"question_id": "team_02", "selected_option_id": "team_02_a"},
        {"question_id": "team_03", "selected_option_id": "team_03_a"},
        {"question_id": "conf_01", "selected_option_id": "conf_01_a"},
        {"question_id": "conf_02", "selected_option_id": "conf_02_a"},
        {"question_id": "conf_03", "selected_option_id": "conf_03_a"},
        {"question_id": "conf_04", "selected_option_id": "conf_04_a"},
    ]
    assert len(answers_payload) == 20

    # Test POST /survey endpoint
    post_res = await authenticated_client.post("/survey", json={"answers": answers_payload})
    assert post_res.status_code == 201
    post_data = post_res.json()
    assert post_data["success"] is True

    result = post_data["data"]
    assert result["responses_recorded"] == 20
    category_scores = result["category_scores"]

    # Verify all 6 categories are represented
    for cat in ["Leadership", "Communication", "Strategy", "Aggression", "Teamwork", "Confidence"]:
        assert cat in category_scores
        assert 0 <= category_scores[cat] <= 100

    # Verify each answer was stored separately
    assert len(result["responses"]) == 20
    for resp in result["responses"]:
        assert "question_id" in resp
        assert "answer" in resp
        assert "score" not in resp  # Scoring logic hidden from client representation

    # Test GET /survey/history endpoint
    history_res = await authenticated_client.get("/survey/history")
    assert history_res.status_code == 200
    history_data = history_res.json()
    assert history_data["success"] is True
    history_list = history_data["data"]
    assert isinstance(history_list, list)

    # Ensure scoring logic is not leaked in history
    for item in history_list:
        assert "question_id" in item
        assert "answer" in item
        assert "score" not in item


@pytest.mark.asyncio
async def test_survey_service_get_user_history_hides_scores():
    """Verify SurveyService.get_user_history returns records without leaking scoring logic."""
    from datetime import datetime, timezone
    import uuid
    from unittest.mock import AsyncMock, MagicMock
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.models.survey_response import SurveyResponse
    from app.services.survey_service import SurveyService

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    now = datetime.now(timezone.utc)
    uid = uuid.uuid4()
    mock_answers = [
        SurveyResponse(
            id=uuid.uuid4(),
            user_id=uid,
            question_id="lead_01",
            category="Leadership",
            answer="Step up, propose a clear synergistic comp, and guide role assignments.",
            score=100,
            created_at=now,
            updated_at=now,
        ),
        SurveyResponse(
            id=uuid.uuid4(),
            user_id=uid,
            question_id="conf_01",
            category="Confidence",
            answer="Thrive under the pressure, isolate 1v1 duels with supreme confidence, and play to win.",
            score=100,
            created_at=now,
            updated_at=now,
        ),
    ]
    mock_result.scalars.return_value.all.return_value = mock_answers
    mock_session.execute.return_value = mock_result

    service = SurveyService(mock_session)
    history = await service.get_user_history(uid)
    assert len(history) == 2
    for record in history:
        dumped = record.model_dump()
        assert "score" not in dumped
        assert "question_id" in dumped
        assert "answer" in dumped
