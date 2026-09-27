"""
Pydantic v2 schemas for Gamer DNA Survey questions, submissions, and history.
"""

from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict, Field


class SurveyOptionPublic(BaseModel):
    """Multiple-choice option exposed to clients (scoring weight is hidden)."""
    id: str = Field(..., description="Unique option identifier", examples=["lead_01_a"])
    text: str = Field(..., description="Behavioral reaction or response choice text")


class SurveyQuestionPublic(BaseModel):
    """Behavioral survey question exposed to clients without internal scoring weights."""
    id: str = Field(..., description="Unique question identifier", examples=["lead_01"])
    category: str = Field(
        ...,
        description="Survey dimension: Leadership, Communication, Strategy, Aggression, Teamwork, Confidence",
    )
    question: str = Field(..., description="Behavioral scenario prompt")
    options: list[SurveyOptionPublic] = Field(..., description="Selectable response options")


class SurveyAnswerSubmission(BaseModel):
    """Single question answer submission."""
    question_id: str = Field(..., description="Identifier of the question answered", examples=["lead_01"])
    selected_option_id: str = Field(..., description="Identifier of the chosen option", examples=["lead_01_a"])


class SurveySubmissionRequest(BaseModel):
    """Complete survey payload containing answers."""
    answers: list[SurveyAnswerSubmission] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Collection of question answers (supports all 20 behavioral questions across 6 categories)",
    )


class SurveyResponseRead(BaseModel):
    """Public representation of an individual recorded survey answer (scoring logic hidden)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="Unique response row identifier")
    user_id: uuid.UUID = Field(..., description="User who submitted this response")
    question_id: str = Field(..., description="Question identifier")
    category: str | None = Field(None, description="Category of the question")
    answer: str = Field(..., description="Selected option text or identifier")
    created_at: datetime = Field(..., description="Timestamp when answered")
    updated_at: datetime = Field(..., description="Timestamp when last modified")


class SurveySubmissionResult(BaseModel):
    """Summary and dimension breakdown returned upon survey submission."""
    message: str = Field(default="Survey submitted and processed successfully.")
    responses_recorded: int = Field(..., description="Number of answers stored")
    category_scores: dict[str, int] = Field(
        ...,
        description="Calculated score breakdown across the 6 dimensions (0-100 scale)",
        examples=[{
            "Leadership": 85,
            "Communication": 90,
            "Strategy": 80,
            "Aggression": 70,
            "Teamwork": 75,
            "Confidence": 85,
        }],
    )
    responses: list[SurveyResponseRead] = Field(..., description="Recorded answers list")
