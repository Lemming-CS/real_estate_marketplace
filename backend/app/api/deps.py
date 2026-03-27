from __future__ import annotations

from collections.abc import Generator

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import decode_access_token
from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.db.enums import RoleCode, UserStatus
from app.db.models import Role, User, UserRole
from app.db.session import get_db_session

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    session = get_db_session()
    try:
        yield session
    finally:
        session.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    user = _resolve_current_user(credentials=credentials, db=db, settings=settings)
    if user is None:
        raise AppError(status_code=401, code="auth_required", message="Authentication is required.")
    return user


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User | None:
    return _resolve_current_user(credentials=credentials, db=db, settings=settings)


def _resolve_current_user(
    *,
    credentials: HTTPAuthorizationCredentials | None,
    db: Session,
    settings: Settings,
) -> User | None:
    if credentials is None:
        return None

    try:
        payload = decode_access_token(settings=settings, token=credentials.credentials)
    except jwt.PyJWTError as exc:
        raise AppError(status_code=401, code="invalid_token", message="Invalid access token.") from exc

    if payload.get("type") != "access":
        raise AppError(status_code=401, code="invalid_token_type", message="Invalid access token type.")

    subject = payload.get("sub")
    if not subject:
        raise AppError(status_code=401, code="token_missing_subject", message="Token subject is missing.")

    user = db.execute(
        select(User).where(User.public_id == subject, User.deleted_at.is_(None))
    ).scalar_one_or_none()
    if user is None or user.status == UserStatus.DELETED:
        raise AppError(status_code=401, code="user_not_found", message="User account is not available.")

    return user


def require_account_status(*allowed_statuses: UserStatus):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.status not in allowed_statuses:
            raise AppError(
                status_code=403,
                code=f"account_{current_user.status.value}",
                message=f"Account status '{current_user.status.value}' is not allowed for this action.",
            )
        return current_user

    return dependency


def require_roles(*required_roles: RoleCode):
    def dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        assigned_roles = set(
            db.execute(
                select(Role.code)
                .join(UserRole, UserRole.role_id == Role.id)
                .where(UserRole.user_id == current_user.id)
            ).scalars()
        )
        if not assigned_roles.intersection(required_roles):
            required = ", ".join(role.value for role in required_roles)
            raise AppError(
                status_code=403,
                code="insufficient_role",
                message=f"One of the following roles is required: {required}.",
            )
        return current_user

    return dependency
