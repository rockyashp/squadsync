"""
Pydantic v2 Base Schema configuration for SquadSync.
"""

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """
    Root base schema with standard Pydantic v2 configuration.
    Enables ORM attribute extraction, population by field name, and extra field prohibition.
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )
