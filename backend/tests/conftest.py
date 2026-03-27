from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from app.core.config import get_settings
from app.db.base import Base
from app.db.enums import RoleCode
from app.db.models import Role
from app.db.session import get_engine, get_session_factory
from app.main import create_app


@pytest.fixture
def test_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[dict[str, object], None, None]:
    database_path = tmp_path / "test.db"
    media_path = tmp_path / "media"

    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{database_path}")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("MEDIA_STORAGE_PATH", str(media_path))

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()

    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    session_factory = get_session_factory()
    with session_factory() as session:
        session.add_all(
            [
                Role(code=RoleCode.ADMIN, name="Administrator", description="Admin"),
                Role(code=RoleCode.USER, name="User", description="User"),
                Role(code=RoleCode.SELLER, name="Seller", description="Seller"),
            ]
        )
        session.commit()

    app = create_app()
    with TestClient(app) as client:
        yield {
            "client": client,
            "session_factory": session_factory,
            "media_path": media_path,
        }

    engine.dispose()
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
