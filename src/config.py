import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env first, then .env.{APP_ENV} on top (later files win).
# Set APP_ENV=test when running tests, APP_ENV=prod in production.
# Defaults to "dev" so local development works without extra config.
_APP_ENV = os.getenv("APP_ENV", "dev")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", f".env.{_APP_ENV}"),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
    )

    project_name: str | None = None
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/main"
    redis_url: str = "redis://localhost:6379/0"

    massive_api_key: str | None = None
    massive_base_url: str = "https://api.massive.ai"


@lru_cache
def get_settings() -> Settings:
    return Settings()
