"""
Main API Router Aggregator for SquadSync.
Handles API versioning and mounts versioned route sets.
"""

from fastapi import APIRouter

from app.api.v1.router import api_v1_router

api_router = APIRouter()

# Mount API version 1 under /v1 (accessed via /api/v1 from main app)
api_router.include_router(api_v1_router, prefix="/v1")
