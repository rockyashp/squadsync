"""
Base service abstraction for Clean Architecture service layers.
"""

from typing import Generic, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")


class BaseService(Generic[ModelType]):
    """
    Base service class providing database session dependency injection.
    Specific domain services inherit from this class.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
