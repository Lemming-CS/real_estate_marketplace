from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import Settings, get_settings
from app.db.enums import UserStatus
from app.db.models import User
from app.modules.auth.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.modules.auth.service import (
    change_password,
    forgot_password,
    login_user,
    logout_session,
    refresh_session,
    register_user,
    reset_password,
)
from app.modules.users.schemas import CurrentUserSchema
from app.modules.users.service import get_current_user_profile

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(
    payload: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    response = register_user(
        db,
        payload=payload,
        settings=settings,
        client_type="mobile",
        user_agent=request.headers.get("user-agent"),
        ip_address=_client_ip(request),
    )
    db.commit()
    return response


@router.post("/login", response_model=TokenResponse, summary="Login with email and password")
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    response = login_user(
        db,
        payload=payload,
        settings=settings,
        client_type="mobile",
        user_agent=request.headers.get("user-agent"),
        ip_address=_client_ip(request),
    )
    db.commit()
    return response


@router.post("/refresh", response_model=TokenResponse, summary="Rotate refresh token and issue a new access token")
def refresh(
    payload: RefreshRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    response = refresh_session(
        db,
        refresh_token=payload.refresh_token,
        settings=settings,
        client_type="mobile",
        user_agent=request.headers.get("user-agent"),
        ip_address=_client_ip(request),
    )
    db.commit()
    return response


@router.post("/logout", response_model=MessageResponse, summary="Revoke the current refresh token")
def logout(payload: LogoutRequest, db: Session = Depends(get_db)) -> MessageResponse:
    logout_session(db, refresh_token=payload.refresh_token)
    db.commit()
    return MessageResponse(message="Logged out successfully.")


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    summary="Generate a password reset token",
)
def request_password_reset(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ForgotPasswordResponse:
    response = forgot_password(db, email=payload.email, settings=settings)
    db.commit()
    return response


@router.post("/reset-password", response_model=MessageResponse, summary="Reset password using a valid token")
def perform_password_reset(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> MessageResponse:
    reset_password(db, payload=payload)
    db.commit()
    return MessageResponse(message="Password has been reset.")


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password for the authenticated user",
)
def perform_password_change(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    change_password(db, user=current_user, payload=payload)
    db.commit()
    return MessageResponse(message="Password has been changed.")


@router.get("/me", response_model=CurrentUserSchema, summary="Return the authenticated user context")
def current_user_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CurrentUserSchema:
    return get_current_user_profile(db, user=current_user)

