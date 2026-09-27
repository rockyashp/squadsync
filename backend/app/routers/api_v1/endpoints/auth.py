"""
Authentication API routes: Register, Login, Refresh, Logout, and Me.
Clean architecture implementation returning unified ApiResponse envelopes.
"""

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import AuthServiceDep, CurrentUser
from app.schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.schemas.common import ApiResponse
from app.schemas.user import UserRead

router = APIRouter()


@router.post(
    "/register",
    response_model=ApiResponse[UserRead],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Registers a new gamer account with unique username, unique email, and strong password.",
)
async def register_user(
    payload: UserRegisterRequest,
    auth_service: AuthServiceDep,
) -> ApiResponse[UserRead]:
    """Register a new user with strong password verification and unique constraints."""
    user = await auth_service.register(payload)
    return ApiResponse.ok(
        data=UserRead.model_validate(user),
        message="User account registered successfully.",
    )


@router.post(
    "/login",
    response_model=ApiResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Log in with JSON credentials",
    description=(
        "Authenticates a user using username or email and password. "
        "Returns a JWT access and refresh token pair in the standard response envelope. "
        "Locks account for security if 5 consecutive failed attempts occur."
    ),
)
async def login_json(
    payload: UserLoginRequest,
    auth_service: AuthServiceDep,
) -> ApiResponse[TokenResponse]:
    """JSON login endpoint for web and mobile frontends."""
    tokens = await auth_service.login(payload)
    return ApiResponse.ok(data=tokens, message="Authentication successful.")


@router.post(
    "/login/oauth2",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=True,
    summary="OAuth2 Form Login (Swagger UI compatibility)",
    description="OAuth2 password form endpoint to support Swagger UI's interactive 'Authorize' button.",
)
async def login_oauth2(
    auth_service: AuthServiceDep,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> TokenResponse:
    """OAuth2 password flow compatibility endpoint for interactive documentation."""
    login_request = UserLoginRequest(
        username_or_email=form_data.username,
        password=form_data.password,
    )
    return await auth_service.login(login_request)


@router.post(
    "/refresh",
    response_model=ApiResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Exchanges a valid, unexpired refresh token for a newly generated access and refresh token pair.",
)
async def refresh_tokens(
    payload: TokenRefreshRequest,
    auth_service: AuthServiceDep,
) -> ApiResponse[TokenResponse]:
    """Exchange refresh token for updated access credentials."""
    tokens = await auth_service.refresh_tokens(payload.refresh_token)
    return ApiResponse.ok(data=tokens, message="Access token renewed successfully.")


@router.post(
    "/logout",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Log out user",
    description="Logs out the currently authenticated user and returns standard response confirmation.",
)
async def logout(
    current_user: CurrentUser,
) -> ApiResponse[None]:
    """Acknowledges user logout and invalidates client session state."""
    return ApiResponse.ok(
        data=None,
        message=f"Goodbye {current_user.username}. Logged out successfully.",
    )


@router.get(
    "/me",
    response_model=ApiResponse[UserRead],
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Retrieves profile information for the authenticated user based on the Bearer access token.",
)
async def get_me(
    current_user: CurrentUser,
) -> ApiResponse[UserRead]:
    """Returns the authenticated user entity wrapped in the ApiResponse envelope."""
    return ApiResponse.ok(
        data=UserRead.model_validate(current_user),
        message="Current user profile retrieved successfully.",
    )


@router.post(
    "/forgot-password",
    response_model=ApiResponse[ForgotPasswordResponse],
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description=(
        "Initiates the password reset workflow for the specified email address. "
        "Returns a generic confirmation message to eliminate user enumeration timing side-channels."
    ),
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    auth_service: AuthServiceDep,
) -> ApiResponse[ForgotPasswordResponse]:
    """Request password reset link/token."""
    response = await auth_service.forgot_password(payload)
    return ApiResponse.ok(
        data=response,
        message=response.message,
    )


@router.post(
    "/reset-password",
    response_model=ApiResponse[ResetPasswordResponse],
    status_code=status.HTTP_200_OK,
    summary="Reset account password",
    description=(
        "Validates the signed password reset token and sets the new strong password. "
        "Unlocks the account and resets failed login attempts."
    ),
)
async def reset_password(
    payload: ResetPasswordRequest,
    auth_service: AuthServiceDep,
) -> ApiResponse[ResetPasswordResponse]:
    """Reset account password using valid reset token."""
    response = await auth_service.reset_password(payload)
    return ApiResponse.ok(
        data=response,
        message=response.message,
    )
