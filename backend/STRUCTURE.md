# SquadSync Backend — Architecture & Folder Structure

## Overview

This is a FastAPI backend organized using a clean layered architecture.

## Directory Map

```
backend/
+-- app/                        # Main application package
¦   +-- main.py                 # App factory, middleware setup, router mounting
¦   +-- config.py               # Re-export shim ? app.core.config (backwards-compat)
¦   +-- database.py             # Re-export shim ? app.core.database (backwards-compat)
¦   ¦
¦   +-- api/                    # ? CANONICAL ROUTING LAYER
¦   ¦   +-- router.py           # Main router: mounts /v1 under /api
¦   ¦   +-- v1/
¦   ¦       +-- router.py       # v1 aggregator: imports all endpoints from routers/
¦   ¦       +-- endpoints/
¦   ¦           +-- health.py   # Health check (lives here, not in routers/)
¦   ¦
¦   +-- routers/                # ? ENDPOINT HANDLER MODULES (imported by api/v1/router.py)
¦   ¦   +-- api_v1/
¦   ¦       +-- api.py          # [LEGACY - NOT USED] superseded by app/api/v1/router.py
¦   ¦       +-- endpoints/      # All v1 endpoint handler files
¦   ¦           +-- admin.py, ai.py, auth.py, chat.py, compatibility.py
¦   ¦           +-- dna.py, explanation.py, friends.py, game.py, matchmaking.py
¦   ¦           +-- news.py, profile.py, riot.py, role_classifier.py
¦   ¦           +-- skill_profile.py, squad_recommendation.py
¦   ¦           +-- steam_dota.py, survey.py, teams.py
¦   ¦           +-- health.py
¦   ¦
¦   +-- core/                   # Application-level singletons & config
¦   ¦   +-- config.py           # Settings (Pydantic BaseSettings)
¦   ¦   +-- database.py         # Async SQLAlchemy engine + session factory
¦   ¦   +-- dependencies.py     # FastAPI dependency injection providers
¦   ¦   +-- exceptions.py       # Centralized exception handlers
¦   ¦   +-- security.py         # JWT & password hashing
¦   ¦   +-- websocket_manager.py
¦   ¦   +-- survey_data.py
¦   ¦   +-- classifier.py
¦   ¦   +-- compatibility/      # Compatibility engine logic
¦   ¦   +-- explanation/        # Explanation engine logic
¦   ¦   +-- matchmaking/        # Matchmaking engine logic
¦   ¦   +-- role_classifier/    # Role classifier logic
¦   ¦   +-- skill_profile/      # Skill profile logic
¦   ¦   +-- squad_recommendation/
¦   ¦
¦   +-- models/                 # SQLAlchemy ORM models
¦   ¦   +-- base.py, user.py, gamer_profile.py, gamer_dna.py
¦   ¦   +-- chat.py, friendship.py, game_account.py, news.py
¦   ¦   +-- player_stat.py, report.py, survey_answer.py
¦   ¦   +-- survey_response.py, team.py
¦   ¦   +-- __init__.py         # Exports Base + all models
¦   ¦
¦   +-- schemas/                # Pydantic request/response schemas
¦   ¦   +-- auth.py, profile.py, dna.py, matchmaking.py, team.py
¦   ¦   +-- compatibility.py, explanation.py, ai.py, riot.py, dota2.py
¦   ¦   +-- game_account.py, role_classifier.py, skill_profile.py
¦   ¦   +-- squad_recommendation.py, survey.py, chat.py, news.py
¦   ¦   +-- admin.py, user.py, friendship.py, health.py
¦   ¦   +-- base.py, common.py
¦   ¦   +-- __init__.py
¦   ¦
¦   +-- services/               # Business logic layer
¦   ¦   +-- auth_service.py, profile_service.py, user_service.py
¦   ¦   +-- ai_service.py, dna_service.py, classifier.py
¦   ¦   +-- matchmaking_service.py, compatibility_service.py
¦   ¦   +-- explanation_service.py, role_classifier_service.py
¦   ¦   +-- skill_profile_service.py, squad_recommendation_service.py
¦   ¦   +-- friendship_service.py, team_service.py, chat_service.py
¦   ¦   +-- news_service.py, admin_service.py, survey_service.py
¦   ¦   +-- game_service.py, riot_service.py, dota2_service.py
¦   ¦   +-- base.py
¦   ¦
¦   +-- repositories/           # Database access layer (CRUD abstractions)
¦   ¦   +-- base.py, user_repository.py, profile_repository.py
¦   ¦   +-- dna_repository.py, game_account_repository.py
¦   ¦   +-- player_stat_repository.py, survey_repository.py
¦   ¦   +-- candidate_repository.py
¦   ¦
¦   +-- providers/              # External API providers (Riot, Steam, OpenDota)
¦   ¦   +-- riot_provider.py, steam_provider.py, opendota_provider.py
¦   ¦   +-- game_provider.py, security_provider.py
¦   ¦   +-- registry.py, dto.py, exceptions.py
¦   ¦   +-- __init__.py
¦   ¦
¦   +-- middleware/             # ASGI middleware
¦   ¦   +-- cors.py             # CORS configuration
¦   ¦   +-- logging.py          # Request logging + correlation IDs
¦   ¦
¦   +-- utils/                  # General utilities
¦       +-- logger.py           # Logging setup helper
¦
+-- alembic/                    # Database migration scripts
¦   +-- env.py
¦   +-- script.py.mako
¦   +-- versions/
¦
+-- tests/                      # Pytest test suite
¦   +-- conftest.py
¦   +-- test_*.py               # 30+ test modules
¦
+-- .env                        # Local secrets (not committed)
+-- .env.example                # Env var template
+-- alembic.ini                 # Alembic configuration
+-- pytest.ini                  # Pytest configuration
+-- requirements.txt            # Python dependencies
```

## Request Flow

```
HTTP Request
    ¦
    ?
main.py (FastAPI app)
    ¦
    +-? CORS Middleware
    +-? RequestLoggingMiddleware
    ¦
    ?
/api/v1/*  --? app.api.router (api_router)
                    ¦
                    ?
              app.api.v1.router (api_v1_router)
                    ¦
                    ?
              app.routers.api_v1.endpoints.*  (endpoint handlers)
                    ¦
                    ?
              app.services.*  (business logic)
                    ¦
                    ?
              app.repositories.*  (database access)
                    ¦
                    ?
              SQLite / PostgreSQL  (via SQLAlchemy async)
```

## Naming Note

The `app/routers/` directory name is slightly confusing — it is NOT where
routers are assembled. It is where **endpoint handler modules** live.
The actual router assembly happens in `app/api/v1/router.py`.
