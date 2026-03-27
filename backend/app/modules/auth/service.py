from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import (
    create_access_token,
    generate_password_reset_token,
    generate_refresh_token,
    hash_token,
    utcnow,
)
from app.core.config import Settings
from app.core.exceptions import AppError
from app.core.security import hash_password, verify_password
from app.db.enums import RoleCode, UserStatus
from app.db.models import PasswordResetToken, RefreshToken, Role, User, UserRole
from app.modules.auth.schemas import (
    AuthUserSchema,
    ChangePasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)


def _get_role_codes(session: Session, *, user_id: int) -> list[str]:
    return [
        role.value
        for role in session.execute(
            select(Role.code).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user_id)
        ).scalars()
    ]


def _build_user_schema(session: Session, user: User) -> AuthUserSchema:
    return AuthUserSchema(
        public_id=user.public_id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        locale=user.locale,
        status=user.status,
        roles=_get_role_codes(session, user_id=user.id),
        profile_image_path=user.profile_image_path,
    )


def _ensure_user_can_login(user: User) -> None:
    if user.status == UserStatus.SUSPENDED:
        raise AppError(status_code=403, code="account_suspended", message="Account is suspended.")
    if user.status == UserStatus.DELETED or user.deleted_at is not None:
        raise AppError(status_code=403, code="account_deleted", message="Account is deactivated.")


def _ensure_user_can_mutate(user: User) -> None:
    if user.status == UserStatus.ACTIVE:
        return
    if user.status == UserStatus.PENDING_VERIFICATION:
        raise AppError(
            status_code=403,
            code="account_pending_verification",
            message="Account verification is still pending.",
        )
    if user.status == UserStatus.SUSPENDED:
        raise AppError(status_code=403, code="account_suspended", message="Account is suspended.")
    raise AppError(status_code=403, code="account_deleted", message="Account is deactivated.")


def _get_role(session: Session, code: RoleCode) -> Role:
    role = session.execute(select(Role).where(Role.code == code)).scalar_one_or_none()
    if role is None:
        default_names = {
            RoleCode.ADMIN: "Administrator",
            RoleCode.USER: "User",
            RoleCode.SELLER: "Seller",
        }
        role = Role(
            code=code,
            name=default_names[code],
            description=f"Auto-created base role '{code.value}'.",
        )
        session.add(role)
        session.flush()
    return role


def _create_refresh_token(
    session: Session,
    *,
    settings: Settings,
    user: User,
    client_type: str,
    user_agent: str | None,
    ip_address: str | None,
) -> str:
    raw_token = generate_refresh_token()
    session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            client_type=client_type,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days),
        )
    )
    return raw_token


def _build_token_response(
    session: Session,
    *,
    settings: Settings,
    user: User,
    refresh_token: str,
) -> TokenResponse:
    roles = _get_role_codes(session, user_id=user.id)
    access_token = create_access_token(settings=settings, subject=user.public_id, roles=roles)
    return TokenResponse(
        access_token=access_token,
        access_token_expires_in=settings.jwt_access_token_expire_minutes * 60,
        refresh_token=refresh_token,
        refresh_token_expires_in=settings.jwt_refresh_token_expire_days * 24 * 60 * 60,
        user=_build_user_schema(session, user),
    )


def register_user(
    session: Session,
    *,
    payload: RegisterRequest,
    settings: Settings,
    client_type: str,
    user_agent: str | None,
    ip_address: str | None,
) -> TokenResponse:
    if session.execute(select(User).where(User.email == payload.email)).scalar_one_or_none():
        raise AppError(status_code=409, code="email_taken", message="Email is already registered.")
    if session.execute(select(User).where(User.username == payload.username)).scalar_one_or_none():
        raise AppError(status_code=409, code="username_taken", message="Username is already taken.")

    user = User(
        email=payload.email,
        username=payload.username,
        full_name=payload.full_name,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        locale=payload.locale,
        status=UserStatus.ACTIVE,
        is_email_verified=False,
    )
    session.add(user)
    session.flush()

    user_role = _get_role(session, RoleCode.USER)
    session.add(UserRole(user_id=user.id, role_id=user_role.id))
    refresh_token = _create_refresh_token(
        session,
        settings=settings,
        user=user,
        client_type=client_type,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    session.flush()
    return _build_token_response(session, settings=settings, user=user, refresh_token=refresh_token)


def login_user(
    session: Session,
    *,
    payload: LoginRequest,
    settings: Settings,
    client_type: str,
    user_agent: str | None,
    ip_address: str | None,
) -> TokenResponse:
    user = session.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise AppError(status_code=401, code="invalid_credentials", message="Invalid email or password.")

    _ensure_user_can_login(user)
    user.last_login_at = utcnow()
    refresh_token = _create_refresh_token(
        session,
        settings=settings,
        user=user,
        client_type=client_type,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    session.flush()
    return _build_token_response(session, settings=settings, user=user, refresh_token=refresh_token)


def refresh_session(
    session: Session,
    *,
    refresh_token: str,
    settings: Settings,
    client_type: str,
    user_agent: str | None,
    ip_address: str | None,
) -> TokenResponse:
    stored_token = session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token))
    ).scalar_one_or_none()
    if (
        stored_token is None
        or stored_token.revoked_at is not None
        or stored_token.expires_at <= utcnow()
    ):
        raise AppError(status_code=401, code="invalid_refresh_token", message="Refresh token is invalid.")

    user = session.execute(select(User).where(User.id == stored_token.user_id)).scalar_one_or_none()
    if user is None:
        raise AppError(status_code=401, code="user_not_found", message="User account is not available.")

    _ensure_user_can_login(user)
    stored_token.revoked_at = utcnow()
    new_refresh_token = _create_refresh_token(
        session,
        settings=settings,
        user=user,
        client_type=client_type,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    session.flush()
    return _build_token_response(session, settings=settings, user=user, refresh_token=new_refresh_token)


def logout_session(session: Session, *, refresh_token: str) -> None:
    stored_token = session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token))
    ).scalar_one_or_none()
    if stored_token is not None and stored_token.revoked_at is None:
        stored_token.revoked_at = utcnow()


def forgot_password(
    session: Session,
    *,
    email: str,
    settings: Settings,
) -> ForgotPasswordResponse:
    user = session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None or user.deleted_at is not None:
        return ForgotPasswordResponse(message="If the account exists, reset instructions have been generated.")

    raw_token = generate_password_reset_token()
    session.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=utcnow() + timedelta(minutes=settings.password_reset_token_expire_minutes),
        )
    )

    debug_token = raw_token if settings.is_debug else None
    return ForgotPasswordResponse(
        message="If the account exists, reset instructions have been generated.",
        debug_reset_token=debug_token,
    )


def reset_password(session: Session, *, payload: ResetPasswordRequest) -> None:
    reset_token = session.execute(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_token(payload.token))
    ).scalar_one_or_none()
    if (
        reset_token is None
        or reset_token.used_at is not None
        or reset_token.expires_at <= utcnow()
    ):
        raise AppError(status_code=400, code="invalid_reset_token", message="Reset token is invalid or expired.")

    user = session.execute(select(User).where(User.id == reset_token.user_id)).scalar_one_or_none()
    if user is None:
        raise AppError(status_code=400, code="user_not_found", message="User account is not available.")

    user.password_hash = hash_password(payload.new_password)
    reset_token.used_at = utcnow()
    for token in session.execute(
        select(RefreshToken).where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
    ).scalars():
        token.revoked_at = utcnow()


def change_password(
    session: Session,
    *,
    user: User,
    payload: ChangePasswordRequest,
) -> None:
    _ensure_user_can_mutate(user)
    if not verify_password(payload.current_password, user.password_hash):
        raise AppError(status_code=400, code="invalid_password", message="Current password is incorrect.")

    user.password_hash = hash_password(payload.new_password)
    for token in session.execute(
        select(RefreshToken).where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
    ).scalars():
        token.revoked_at = utcnow()
