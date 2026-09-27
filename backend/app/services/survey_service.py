"""
Survey service handling question catalog retrieval, answer scoring, and response persistence.
Delegates database queries to SurveyRepository conforming to the Repository Pattern (SOLID - SRP & DIP).
"""

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.survey_data import (
    get_all_questions_public,
    get_option_evaluation,
    get_question_by_id,
)
from app.models.survey_response import SurveyResponse
from app.repositories.survey_repository import SurveyRepository
from app.schemas.survey import (
    SurveyQuestionPublic,
    SurveyResponseRead,
    SurveySubmissionRequest,
    SurveySubmissionResult,
)
from app.services.base import BaseService


class SurveyService(BaseService[SurveyResponse]):
    """Encapsulates survey business logic: question delivery, answer validation, scoring, and persistence."""

    def __init__(
        self,
        db: AsyncSession,
        survey_repo: SurveyRepository | None = None,
    ) -> None:
        super().__init__(db)
        self.survey_repo = survey_repo or SurveyRepository(db)

    def get_public_questions(self) -> list[SurveyQuestionPublic]:
        """
        Retrieves the 20 behavioral questions with weights stripped out to protect scoring integrity.
        """
        raw_questions = get_all_questions_public()
        return [SurveyQuestionPublic.model_validate(q) for q in raw_questions]

    async def submit_survey(
        self,
        user_id: uuid.UUID,
        submission: SurveySubmissionRequest,
    ) -> SurveySubmissionResult:
        """
        Processes submitted answers, scores each question server-side,
        and stores every answer as an individual record in survey_answers.
        """
        category_totals: dict[str, list[int]] = defaultdict(list)
        saved_records: list[SurveyResponse] = []

        # Process each submitted answer
        for item in submission.answers:
            question_data = get_question_by_id(item.question_id)
            if not question_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown question identifier: '{item.question_id}'",
                )

            opt_eval = get_option_evaluation(item.selected_option_id)
            if not opt_eval or opt_eval["question_id"] != item.question_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Option '{item.selected_option_id}' is invalid for question '{item.question_id}'",
                )

            category = opt_eval["category"]
            score = opt_eval["score"]
            answer_text = opt_eval["text"]

            category_totals[category].append(score)

            # Store every answer separately; upsert if question already answered
            stmt = select(SurveyResponse).where(
                SurveyResponse.user_id == user_id,
                SurveyResponse.question_id == item.question_id,
            )
            existing_response = (await self.db.execute(stmt)).scalar_one_or_none()

            if existing_response:
                existing_response.category = category
                existing_response.answer = answer_text
                existing_response.score = score
                existing_response.selected_option_id = item.selected_option_id
                saved_records.append(existing_response)
            else:
                now = datetime.now(timezone.utc)
                new_response = SurveyResponse(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    question_id=item.question_id,
                    selected_option_id=item.selected_option_id,
                    category=category,
                    answer=answer_text,
                    score=score,
                    created_at=now,
                    updated_at=now,
                )
                self.db.add(new_response)
                saved_records.append(new_response)

        await self.db.commit()

        # Refresh instances to capture generated timestamps and UUIDs
        for rec in saved_records:
            await self.db.refresh(rec)

        # Compute rounded average score per category
        category_scores: dict[str, int] = {}
        for cat, scores in category_totals.items():
            category_scores[cat] = round(sum(scores) / len(scores)) if scores else 0

        # Sort saved records for deterministic output
        saved_records.sort(key=lambda r: r.question_id)

        # Automatically update GamerDNA profile upon survey submission
        from app.services.dna_service import DNAService
        dna_service = DNAService(self.db)
        await dna_service.classify_and_store(user_id, responses=saved_records)

        return SurveySubmissionResult(
            message="Survey answers recorded and Gamer DNA classified successfully.",
            responses_recorded=len(saved_records),
            category_scores=category_scores,
            responses=[SurveyResponseRead.model_validate(r) for r in saved_records],
        )

    async def get_user_history(self, user_id: uuid.UUID) -> list[SurveyResponseRead]:
        """
        Retrieves all individually stored survey responses for the given user via SurveyRepository.
        """
        responses = await self.survey_repo.get_answers_by_user_id(user_id)
        return [SurveyResponseRead.model_validate(r) for r in responses]
