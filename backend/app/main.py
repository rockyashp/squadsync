"""
Main application factory and lifespan manager for SquadSync.
Initializes FastAPI app, middleware, routers, and exception handlers.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from app.api.router import api_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import close_db_connection, engine
from app.core.exceptions import register_exception_handlers
from app.middleware.cors import setup_cors_middleware
from app.middleware.logging import RequestLoggingMiddleware
from app.models import Base
from app.routers.api_v1.endpoints.ai import router as ai_router
from app.routers.api_v1.endpoints.matchmaking import router as matchmaking_router
from app.routers.api_v1.endpoints.survey import router as survey_router
from app.utils.logger import setup_logging

logger = logging.getLogger("squadsync.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan context manager.
    Handles startup configuration and graceful teardown of resources.
    """
    # Startup lifecycle
    setup_logging()
    logger.info(
        "Starting %s (Version: %s, Environment: %s)...",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.ENVIRONMENT.value,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified/created successfully.")
    yield
    # Shutdown lifecycle
    logger.info("Initiating graceful shutdown for %s...", settings.APP_NAME)
    await close_db_connection()
    logger.info("Graceful shutdown complete.")


def create_application() -> FastAPI:
    """
    Application factory instantiating and configuring the FastAPI instance.
    """
    app = FastAPI(
        title=f"{settings.APP_NAME} API",
        version=settings.APP_VERSION,
        description="Production-ready FastAPI backend for SquadSync - Team Matching & Gamer Analytics.",
        openapi_url="/openapi.json" if settings.ENABLE_SWAGGER else None,
        docs_url="/docs" if settings.ENABLE_SWAGGER else None,
        redoc_url="/redoc" if settings.ENABLE_SWAGGER else None,
        lifespan=lifespan,
    )

    # 1. Attach CORS Middleware
    setup_cors_middleware(app)

    # 2. Attach Request Logging & Correlation ID Middleware
    app.add_middleware(RequestLoggingMiddleware)

    # 3. Register Centralized Exception Handlers
    register_exception_handlers(app)

    # 4. Root Health Check Endpoint & Root Welcome Route
    app.include_router(health_router, tags=["Health"])

    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "status": "online",
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "documentation": "/docs",
            "health": "/health",
            "api_v1": "/api/v1"
        }

    # 5. Versioned API Routers
    # Mounts /api/v1 (and future /api/v2) cleanly without duplication
    app.include_router(api_router, prefix="/api")

    # Mount /survey, /matchmaking, and /ai direct endpoints for non-prefixed client access
    app.include_router(survey_router, prefix="/survey", include_in_schema=False)
    app.include_router(matchmaking_router, prefix="/matchmaking", include_in_schema=False)
    app.include_router(ai_router, include_in_schema=False)

    return app


# Application singleton
app: FastAPI = create_application()
