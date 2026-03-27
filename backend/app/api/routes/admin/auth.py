from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.routes.auth import _client_ip
from app.api.deps import get_db
from app.core.exceptions import AppError
from app.core.config import Settings, get_settings
from app.modules.auth.schemas import LoginRequest, TokenResponse
from app.modules.auth.service import login_user, logout_session

router = APIRouter(prefix="/admin/auth", tags=["admin-auth"])


@router.post("/login", response_model=TokenResponse, summary="Login to the admin panel")
def admin_login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    response = login_user(
        db,
        payload=payload,
        settings=settings,
        client_type="admin",
        user_agent=request.headers.get("user-agent"),
        ip_address=_client_ip(request),
    )
    if "admin" not in response.user.roles:
        logout_session(db, refresh_token=response.refresh_token)
        raise AppError(status_code=403, code="admin_access_required", message="Admin access is required.")
    db.commit()
    return response
