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

    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_database: str = "marketplace_db"
    mysql_user: str = "appuser"
    mysql_password: str = "apppass"

    smtp_host: str = "127.0.0.1"
    smtp_port: int = 1025

    @field_validator("app_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @computed_field
    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )

    @property
    def is_debug(self) -> bool:
        return self.app_env.lower() in {"local", "development", "dev"}


@lru_cache
def get_settings() -> Settings:
    return Settings()

