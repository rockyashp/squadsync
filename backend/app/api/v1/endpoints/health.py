"""
Health check endpoints for application and database status.
Clean architecture implementation returning unified ApiResponse envelopes.
"""

import time

from fastapi import APIRouter, status
from sqlalchemy import text

from app.core.config import settings
from app.core.dependencies import DatabaseSession
from app.schemas.common import ApiResponse
from app.schemas.health import DatabaseHealth, HealthCheck

router = APIRouter()


@router.get(
    "/health",
    response_model=ApiResponse[HealthCheck],
    status_code=status.HTTP_200_OK,
    summary="Application Health & Database Connectivity Check",
    description="Returns the running status of the API service along with database ping latency.",
)
async def check_health(db: DatabaseSession) -> ApiResponse[HealthCheck]:
    """
    Health check endpoint that verifies API state and database connectivity.
    Pings PostgreSQL with 'SELECT 1' and calculates roundtrip latency in milliseconds.
    """
    start_time = time.perf_counter()
    db_status = "connected"
    latency_ms: float | None = None
    overall_status = "healthy"

    try:
        # Ping the database using a lightweight query
        await db.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
    except Exception:
        db_status = "disconnected"
        overall_status = "degraded"

    health_info = HealthCheck(
        status=overall_status,
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT.value,
        database=DatabaseHealth(
            status=db_status,
            latency_ms=latency_ms,
        ),
    )
    return ApiResponse.ok(
        data=health_info,
        message=f"{settings.APP_NAME} is {overall_status}.",
    )
