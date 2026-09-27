"""
Pydantic Schemas Package.
"""

from app.schemas.auth import (
    LogoutResponse,
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.schemas.common import ErrorResponse, MessageResponse, PaginatedResponse
from app.schemas.dna import (
    GamerDNABase,
    GamerDNACardResponse,
    GamerDNAEvaluationResponse,
    GamerDNARead,
    ProfileCardSummary,
)
from app.schemas.dota2 import (
    Dota2HeroStat,
    Dota2RecentMatch,
    Dota2SyncResponse,
    Dota2TelemetrySummary,
    SteamLoginUrlResponse,
)
from app.schemas.game_account import (
    GameAccountLinkRequest,
    GameAccountRead,
    GameAccountSyncResponse,
    GameAccountUpdateRequest,
    PlayerStatRead,
)
from app.schemas.health import DatabaseHealth, HealthCheck
from app.schemas.profile import (
    GamerProfileBase,
    GamerProfileCreate,
    GamerProfileRead,
    GamerProfileUpdate,
)
from app.schemas.riot import (
    RiotCallbackRequest,
    RiotLoginUrlResponse,
    RiotSyncResponse,
    RiotTelemetrySummary,
)
from app.schemas.survey import (
    SurveyAnswerSubmission,
    SurveyOptionPublic,
    SurveyQuestionPublic,
    SurveyResponseRead,
    SurveySubmissionRequest,
    SurveySubmissionResult,
)
from app.schemas.user import UserBase, UserRead

__all__ = [
    "ErrorResponse",
    "MessageResponse",
    "PaginatedResponse",
    "HealthCheck",
    "DatabaseHealth",
    "UserBase",
    "UserRead",
    "UserRegisterRequest",
    "UserLoginRequest",
    "TokenResponse",
    "TokenRefreshRequest",
    "LogoutResponse",
    "GamerProfileBase",
    "GamerProfileCreate",
    "GamerProfileRead",
    "GamerProfileUpdate",
    "SurveyOptionPublic",
    "SurveyQuestionPublic",
    "SurveyAnswerSubmission",
    "SurveySubmissionRequest",
    "SurveyResponseRead",
    "SurveySubmissionResult",
    "GamerDNABase",
    "GamerDNARead",
    "GamerDNAEvaluationResponse",
    "GamerDNACardResponse",
    "ProfileCardSummary",
    "GameAccountLinkRequest",
    "GameAccountUpdateRequest",
    "GameAccountRead",
    "PlayerStatRead",
    "GameAccountSyncResponse",
    "SteamLoginUrlResponse",
    "Dota2HeroStat",
    "Dota2RecentMatch",
    "Dota2TelemetrySummary",
    "Dota2SyncResponse",
    "RiotLoginUrlResponse",
    "RiotCallbackRequest",
    "RiotTelemetrySummary",
    "RiotSyncResponse",
]
