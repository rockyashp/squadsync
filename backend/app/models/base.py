"""
SQLAlchemy 2.0 Base Model, mixins, and explicit PostgreSQL naming conventions.
"""

from datetime import datetime
import re
from typing import Any
import uuid

from sqlalchemy import DateTime, MetaData, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

# Explicit naming convention for database constraints and indexes (crucial for Alembic)
POSTGRES_INDEXES_NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def camel_to_snake(name: str) -> str:
    """Convert PascalCase/CamelCase string to snake_case."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


class Base(DeclarativeBase):
    """
    Base Declarative class for all SQLAlchemy 2.0 ORM models in SquadSync.
    Automatically generates table names from class names in snake_case plural.
    """

    metadata = MetaData(naming_convention=POSTGRES_INDEXES_NAMING_CONVENTION)

    @declared_attr.directive
    def __tablename__(cls) -> str:
        name = camel_to_snake(cls.__name__)
        if not name.endswith("s"):
            return name + "s"
        return name


class UUIDPrimaryKeyMixin:
    """
    Mixin providing a standard UUID primary key.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False,
    )


class TimestampMixin:
    """
    Mixin providing timezone-aware created_at and updated_at timestamps.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
