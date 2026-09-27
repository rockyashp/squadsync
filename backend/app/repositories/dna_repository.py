"""
DNARepository implementation.
Decouples GamerDNA querying and persistence from the domain layer.
Conforms to SQLAlchemy 2.0 and the Repository Pattern (SOLID - SRP & DIP).
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gamer_dna import GamerDNA
from app.repositories.base import BaseRepository


class DNARepository(BaseRepository[GamerDNA]):
    """
    Repository handling persistence and querying of GamerDNA records.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(GamerDNA, db)

    async def get_by_user_id(self, user_id: uuid.UUID) -> GamerDNA | None:
        """Fetch the GamerDNA profile for a specific user."""
        stmt = select(GamerDNA).where(GamerDNA.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_dna(self, dna: GamerDNA) -> GamerDNA:
        """Create or update a user's GamerDNA profile atomically."""
        existing = await self.get_by_user_id(dna.user_id)
        if existing:
            existing.primary_role = dna.primary_role
            existing.secondary_role = dna.secondary_role
            existing.personality = dna.personality
            existing.reasoning = dna.reasoning
            existing.leadership = dna.leadership
            existing.communication = dna.communication
            existing.strategy = dna.strategy
            existing.aggression = dna.aggression
            existing.teamwork = dna.teamwork
            existing.confidence = dna.confidence
            existing.raw_evaluation = dna.raw_evaluation
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        return await self.create(dna)
