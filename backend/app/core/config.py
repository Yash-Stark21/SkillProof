"""Environment-backed application settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime configuration loaded from process environment or ``backend/.env``."""

    database_url: str = Field(
        default="postgresql+psycopg://skillproof:skillproof@localhost:5432/skillproof",
        validation_alias="DATABASE_URL",
    )
    test_database_url: str | None = Field(default=None, validation_alias="TEST_DATABASE_URL")

    model_config = SettingsConfigDict(
        env_file=_BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return one immutable-by-convention settings snapshot per process."""

    return Settings()
