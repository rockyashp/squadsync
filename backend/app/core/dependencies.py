"""
FastAPI dependency injection utilities for database sessions, repositories, services, and current user security.
"""

from typing import Annotated, Any
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import TokenTypes, UNAUTHORIZED_ERROR_MSG
from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.providers.registry import GameProviderRegistry, provider_registry
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.dna_repository import DNARepository
from app.repositories.game_account_repository import GameAccountRepository
from app.repositories.player_stat_repository import PlayerStatRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.survey_repository import SurveyRepository
from app.repositories.user_repository import UserRepository
from app.services.ai_service import AIService
from app.services.auth_service import AuthService
from app.services.dna_service import DNAService
from app.services.dota2_service import Dota2Service
from app.services.game_service import GameService
from app.services.matchmaking_service import MatchmakingService
from app.services.profile_service import ProfileService
from app.services.riot_service import RiotService
from app.services.compatibility_service import AICompatibilityService
from app.services.explanation_service import AIExplanationService
from app.services.role_classifier_service import RoleClassifierService
from app.services.skill_profile_service import SkillProfileService
from app.services.squad_recommendation_service import SquadRecommendationService
from app.services.survey_service import SurveyService
from app.services.user_service import UserService

# Database session dependency annotation
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]

# OAuth2 scheme for Swagger UI authorization button
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login/oauth2",
    auto_error=True,
)


# ------------------------------------------------------------------------------
# Repository Providers
# ------------------------------------------------------------------------------

def get_user_repository(db: DatabaseSession) -> UserRepository:
    """Dependency provider for UserRepository."""
    return UserRepository(db)


def get_profile_repository(db: DatabaseSession) -> ProfileRepository:
    """Dependency provider for ProfileRepository."""
    return ProfileRepository(db)


def get_survey_repository(db: DatabaseSession) -> SurveyRepository:
    """Dependency provider for SurveyRepository."""
    return SurveyRepository(db)


def get_dna_repository(db: DatabaseSession) -> DNARepository:
    """Dependency provider for DNARepository."""
    return DNARepository(db)


def get_game_account_repository(db: DatabaseSession) -> GameAccountRepository:
    """Dependency provider for GameAccountRepository."""
    return GameAccountRepository(db)


def get_player_stat_repository(db: DatabaseSession) -> PlayerStatRepository:
    """Dependency provider for PlayerStatRepository."""
    return PlayerStatRepository(db)


def get_candidate_repository(db: DatabaseSession) -> CandidateRepository:
    """Dependency provider for CandidateRepository."""
    return CandidateRepository(db)


def get_game_provider_registry() -> GameProviderRegistry:
    """Dependency provider for GameProviderRegistry."""
    return provider_registry


# ------------------------------------------------------------------------------
# Service Providers
# ------------------------------------------------------------------------------

def get_user_service(
    db: DatabaseSession,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    """Dependency provider for UserService."""
    return UserService(db, user_repo=user_repo)


def get_auth_service(
    db: DatabaseSession,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> AuthService:
    """Dependency provider for AuthService."""
    return AuthService(db, user_service=user_service)


def get_profile_service(
    db: DatabaseSession,
    profile_repo: Annotated[ProfileRepository, Depends(get_profile_repository)],
) -> ProfileService:
    """Dependency provider for ProfileService."""
    return ProfileService(db, profile_repo=profile_repo)


def get_survey_service(
    db: DatabaseSession,
    survey_repo: Annotated[SurveyRepository, Depends(get_survey_repository)],
) -> SurveyService:
    """Dependency provider for SurveyService."""
    return SurveyService(db, survey_repo=survey_repo)


def get_dna_service(
    db: DatabaseSession,
    dna_repo: Annotated[DNARepository, Depends(get_dna_repository)],
    survey_repo: Annotated[SurveyRepository, Depends(get_survey_repository)],
) -> DNAService:
    """Dependency provider for DNAService."""
    return DNAService(db, dna_repo=dna_repo, survey_repo=survey_repo)


def get_game_service(
    db: DatabaseSession,
    account_repo: Annotated[GameAccountRepository, Depends(get_game_account_repository)],
    stat_repo: Annotated[PlayerStatRepository, Depends(get_player_stat_repository)],
    registry: Annotated[GameProviderRegistry, Depends(get_game_provider_registry)],
) -> GameService:
    """Dependency provider for GameService."""
    return GameService(db, account_repo=account_repo, stat_repo=stat_repo, registry=registry)


def get_dota2_service(
    db: DatabaseSession,
    account_repo: Annotated[GameAccountRepository, Depends(get_game_account_repository)],
    stat_repo: Annotated[PlayerStatRepository, Depends(get_player_stat_repository)],
) -> Dota2Service:
    """Dependency provider for Dota2Service."""
    return Dota2Service(db, account_repo=account_repo, stat_repo=stat_repo)


def get_riot_service(
    db: DatabaseSession,
    account_repo: Annotated[GameAccountRepository, Depends(get_game_account_repository)],
    stat_repo: Annotated[PlayerStatRepository, Depends(get_player_stat_repository)],
) -> RiotService:
    """Dependency provider for RiotService."""
    return RiotService(db, account_repo=account_repo, stat_repo=stat_repo)


def get_matchmaking_service(db: DatabaseSession) -> MatchmakingService:
    """Dependency provider for MatchmakingService."""
    return MatchmakingService(db)


def get_role_classifier_service(
    db: DatabaseSession,
    dna_repo: Annotated[DNARepository, Depends(get_dna_repository)],
    player_stat_repo: Annotated[PlayerStatRepository, Depends(get_player_stat_repository)],
    profile_repo: Annotated[ProfileRepository, Depends(get_profile_repository)],
) -> RoleClassifierService:
    """Dependency provider for RoleClassifierService."""
    return RoleClassifierService(
        db=db,
        dna_repo=dna_repo,
        player_stat_repo=player_stat_repo,
        profile_repo=profile_repo,
    )


def get_skill_profile_service(
    db: DatabaseSession,
    dna_repo: Annotated[DNARepository, Depends(get_dna_repository)],
    player_stat_repo: Annotated[PlayerStatRepository, Depends(get_player_stat_repository)],
    survey_repo: Annotated[SurveyRepository, Depends(get_survey_repository)],
) -> SkillProfileService:
    """Dependency provider for SkillProfileService."""
    return SkillProfileService(
        db=db,
        dna_repo=dna_repo,
        player_stat_repo=player_stat_repo,
        survey_repo=survey_repo,
    )


def get_ai_compatibility_service(
    db: DatabaseSession,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    profile_repo: Annotated[ProfileRepository, Depends(get_profile_repository)],
    dna_repo: Annotated[DNARepository, Depends(get_dna_repository)],
    player_stat_repo: Annotated[PlayerStatRepository, Depends(get_player_stat_repository)],
) -> AICompatibilityService:
    """Dependency provider for AICompatibilityService."""
    return AICompatibilityService(
        db=db,
        user_repo=user_repo,
        profile_repo=profile_repo,
        dna_repo=dna_repo,
        player_stat_repo=player_stat_repo,
    )


def get_squad_recommendation_service(
    db: DatabaseSession,
    candidate_repo: Annotated[CandidateRepository, Depends(get_candidate_repository)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> SquadRecommendationService:
    """Dependency provider for SquadRecommendationService."""
    return SquadRecommendationService(
        db=db,
        candidate_repo=candidate_repo,
        user_repo=user_repo,
    )


def get_explanation_service(
    db: DatabaseSession,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    profile_repo: Annotated[ProfileRepository, Depends(get_profile_repository)],
    dna_repo: Annotated[DNARepository, Depends(get_dna_repository)],
    player_stat_repo: Annotated[PlayerStatRepository, Depends(get_player_stat_repository)],
) -> AIExplanationService:
    """Dependency provider for AIExplanationService."""
    return AIExplanationService(
        db=db,
        user_repo=user_repo,
        profile_repo=profile_repo,
        dna_repo=dna_repo,
        player_stat_repo=player_stat_repo,
    )


def get_ai_service(
    db: DatabaseSession,
    dna_service: Annotated[DNAService, Depends(get_dna_service)],
    role_classifier_service: Annotated[RoleClassifierService, Depends(get_role_classifier_service)],
    skill_profile_service: Annotated[SkillProfileService, Depends(get_skill_profile_service)],
    compatibility_service: Annotated[AICompatibilityService, Depends(get_ai_compatibility_service)],
    squad_service: Annotated[SquadRecommendationService, Depends(get_squad_recommendation_service)],
    explanation_service: Annotated[AIExplanationService, Depends(get_explanation_service)],
) -> AIService:
    """Dependency provider for the unified AIService."""
    return AIService(
        db=db,
        dna_service=dna_service,
        role_classifier_service=role_classifier_service,
        skill_profile_service=skill_profile_service,
        compatibility_service=compatibility_service,
        squad_service=squad_service,
        explanation_service=explanation_service,
    )


# ------------------------------------------------------------------------------
# Type Aliases for Clean Router Signatures
# ------------------------------------------------------------------------------

UserRepoDep = Annotated[UserRepository, Depends(get_user_repository)]
ProfileRepoDep = Annotated[ProfileRepository, Depends(get_profile_repository)]
SurveyRepoDep = Annotated[SurveyRepository, Depends(get_survey_repository)]
DNARepoDep = Annotated[DNARepository, Depends(get_dna_repository)]
GameAccountRepoDep = Annotated[GameAccountRepository, Depends(get_game_account_repository)]
PlayerStatRepoDep = Annotated[PlayerStatRepository, Depends(get_player_stat_repository)]
CandidateRepoDep = Annotated[CandidateRepository, Depends(get_candidate_repository)]

UserServiceDep = Annotated[UserService, Depends(get_user_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
ProfileServiceDep = Annotated[ProfileService, Depends(get_profile_service)]
SurveyServiceDep = Annotated[SurveyService, Depends(get_survey_service)]
DNAServiceDep = Annotated[DNAService, Depends(get_dna_service)]
GameServiceDep = Annotated[GameService, Depends(get_game_service)]
Dota2ServiceDep = Annotated[Dota2Service, Depends(get_dota2_service)]
RiotServiceDep = Annotated[RiotService, Depends(get_riot_service)]
MatchmakingServiceDep = Annotated[MatchmakingService, Depends(get_matchmaking_service)]
RoleClassifierServiceDep = Annotated[RoleClassifierService, Depends(get_role_classifier_service)]
SkillProfileServiceDep = Annotated[SkillProfileService, Depends(get_skill_profile_service)]
AICompatibilityServiceDep = Annotated[AICompatibilityService, Depends(get_ai_compatibility_service)]
SquadRecommendationServiceDep = Annotated[SquadRecommendationService, Depends(get_squad_recommendation_service)]
AIExplanationServiceDep = Annotated[AIExplanationService, Depends(get_explanation_service)]
AIServiceDep = Annotated[AIService, Depends(get_ai_service)]


# ------------------------------------------------------------------------------
# Authentication Dependencies
# ------------------------------------------------------------------------------

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_service: UserServiceDep,
) -> User:
    """
    Extracts Bearer token from authorization header, validates JWT signature and claims,
    and returns the corresponding User entity.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=UNAUTHORIZED_ERROR_MSG,
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception

    # Enforce that the provided token is an access token
    token_type = payload.get("type")
    if token_type != TokenTypes.ACCESS.value:
        raise credentials_exception

    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise credentials_exception

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    user = await user_service.get_by_id(user_id)
    if not user:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Ensures that the authenticated user is currently active and not locked.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account.",
        )
    if current_user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked due to multiple failed login attempts.",
        )
    return current_user


# Type alias for endpoints requiring an active authenticated user
CurrentUser = Annotated[User, Depends(get_current_active_user)]


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """Enforces administrator role authorization (BR-4)."""
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required.",
        )
    return current_user


CurrentAdminUser = Annotated[User, Depends(get_current_admin_user)]
