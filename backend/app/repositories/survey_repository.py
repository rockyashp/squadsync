"""
SurveyRepository implementation.
Decouples survey answer querying and bulk persistence from the domain layer.
Conforms to SQLAlchemy 2.0 and the Repository Pattern (SOLID - SRP & DIP).
"""

from collections.abc import Sequence
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.survey_answer import SurveyAnswer
from app.repositories.base import BaseRepository


class SurveyRepository(BaseRepository[SurveyAnswer]):
    """
    Repository handling persistence and querying of SurveyAnswer records.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(SurveyAnswer, db)

    async def get_answers_by_user_id(self, user_id: uuid.UUID) -> Sequence[SurveyAnswer]:
        """Fetch all individual survey answers submitted by a user."""
        stmt = (
            select(SurveyAnswer)
            .where(SurveyAnswer.user_id == user_id)
            .order_by(SurveyAnswer.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_latest_answers_by_user_id(self, user_id: uuid.UUID) -> Sequence[SurveyAnswer]:
        """Fetch latest survey answers submitted by a user."""
        return await self.get_answers_by_user_id(user_id)

    async def save_answers(self, answers: list[SurveyAnswer]) -> list[SurveyAnswer]:
        """Bulk save submitted survey answers in an atomic operation."""
        for ans in answers:
            self.db.add(ans)
        await self.db.commit()
        for ans in answers:
            await self.db.refresh(ans)
        return answers
