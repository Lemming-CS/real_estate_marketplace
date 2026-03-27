from __future__ import annotations

from functools import lru_cache

from pydantic import computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Electronics Marketplace API"
    app_env: str = "local"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_log_level: str = "INFO"
    app_cors_origins: list[str] = []
    media_storage_path: str = "uploads"

    database_url: str | None = None
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_database: str = "marketplace_db"
    mysql_user: str = "appuser"
    mysql_password: str = "apppass"

    smtp_host: str = "127.0.0.1"
    smtp_port: int = 1025
    mock_payment_checkout_base_url: str = "http://localhost:8000/api/v1"

    jwt_secret_key: str = "change-me-in-real-env"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 30
    password_reset_token_expire_minutes: int = 30

    @field_validator("app_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @computed_field
    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )

    @property
    def is_debug(self) -> bool:
        return self.app_env.lower() in {"local", "development", "dev", "test"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
