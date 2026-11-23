from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_mode: Literal["demo", "official"] = "official"
    metrics_enabled: bool = False
    database_url: str = "sqlite:///./aquamaroc.db"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    raw_archive_dir: Path = Path("data/archive")
    demo_forecast_path: Path | None = None

    @field_validator("database_url")
    @classmethod
    def valid_database_url(cls, value: str) -> str:
        url = make_url(value)
        if url.get_backend_name() not in {"sqlite", "postgresql"}:
            raise ValueError("Seuls PostgreSQL et SQLite (tests/démo locale) sont acceptés")
        return value

    @field_validator("cors_origins")
    @classmethod
    def explicit_origins(cls, value: list[str]) -> list[str]:
        if any(origin == "*" or not origin.startswith(("http://", "https://")) for origin in value):
            raise ValueError("Configurer des origines HTTP(S) explicites")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
