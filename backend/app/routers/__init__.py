"""
Endpoint Handlers Package (app.routers).

This package contains endpoint handler modules organized by API version.
The endpoint files here are imported and mounted by the canonical router
aggregator at: app/api/v1/router.py

Directory Layout:
    routers/
    └── api_v1/
        └── endpoints/      ← All v1 endpoint handler modules
            ├── admin.py
            ├── ai.py
            ├── auth.py
            ├── chat.py
            ├── compatibility.py
            ├── dna.py
            ├── explanation.py
            ├── friends.py
            ├── game.py
            ├── health.py
            ├── matchmaking.py
            ├── news.py
            ├── profile.py
            ├── riot.py
            ├── role_classifier.py
            ├── skill_profile.py
            ├── squad_recommendation.py
            ├── steam_dota.py
            ├── survey.py
            └── teams.py

NOTE: Do NOT import from routers.api_v1.api (legacy file, not in use).
      Use app.api.v1.router for the authoritative router aggregator.
"""
