"""
Generic SQLAlchemy 2.0 Base Repository pattern implementation.
Decouples data access, query building, and persistence from domain and service layers.
"""

from collections.abc import Sequence
from typing import Any, Generic, TypeVar
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic repository providing standard asynchronous CRUD operations for SQLAlchemy 2.0 models.
    """

    def __init__(self, model: type[ModelType], db: AsyncSession) -> None:
        self.model = model
        self.db = db

    async def get_by_id(self, entity_id: uuid.UUID | Any) -> ModelType | None:
        """Fetch a single record by its primary key."""
        return await self.db.get(self.model, entity_id)

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[ModelType]:
        """Fetch a paginated collection of records."""
        stmt = select(self.model).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create(self, entity: ModelType) -> ModelType:
        """Persist a new model instance and commit transaction."""
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def update(self, entity: ModelType) -> ModelType:
        """Flush changes to an existing model instance and commit transaction."""
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def delete(self, entity: ModelType) -> None:
        """Remove a model instance from the database."""
        await self.db.delete(entity)
        await self.db.commit()

    async def count(self) -> int:
        """Return the total number of records for this entity."""
        stmt = select(func.count()).select_from(self.model)
        result = await self.db.execute(stmt)
        return result.scalar_one() or 0
