"""
Pydantic v2 schemas for application health check responses.
"""

from datetime import datetime, timezone
from pydantic import BaseModel, Field


class DatabaseHealth(BaseModel):
    """Database connectivity status detail."""
    status: str = Field(..., description="Status of DB connection: 'connected' or 'disconnected'")
    latency_ms: float | None = Field(None, description="Roundtrip query latency in milliseconds")


class HealthCheck(BaseModel):
    """Comprehensive service health report."""
    status: str = Field(default="healthy", description="Overall health state ('healthy' or 'unhealthy')")
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Running application version")
    environment: str = Field(..., description="Deployment environment")
    database: DatabaseHealth = Field(..., description="Database connectivity status")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the health check evaluation",
    )
