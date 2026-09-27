"""
[LEGACY - NOT IN USE] API v1 Router Aggregator.

This file is superseded by app/api/v1/router.py and is NOT imported by main.py.
It was an early iteration of the router aggregator before the app/api/ structure was established.

The canonical API v1 router is: app.api.v1.router.api_v1_router
All endpoints are registered there via imports from app.routers.api_v1.endpoints.*

Do NOT import from this file.
"""

from fastapi import APIRouter

from app.routers.api_v1.endpoints import auth, dna, game, health, matchmaking, profile, riot, steam_dota, survey

api_router = APIRouter()

# Include version 1 endpoints
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(profile.router, prefix="/profile", tags=["Gamer Profile"])
api_router.include_router(survey.router, prefix="/survey", tags=["Gamer DNA Survey"])
api_router.include_router(dna.router, prefix="/dna", tags=["Gamer DNA Classification"])
api_router.include_router(matchmaking.router, prefix="/matchmaking", tags=["Matchmaking Engine"])
api_router.include_router(game.router, prefix="/games", tags=["Game Integration"])
api_router.include_router(steam_dota.router, prefix="/games", tags=["Steam & Dota 2"])
api_router.include_router(riot.router, prefix="/games", tags=["Riot Games"])
