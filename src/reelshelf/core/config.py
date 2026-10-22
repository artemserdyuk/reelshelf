from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]

ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="REELSHELF_",
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    app_name: str = Field(
        default="ReelShelf API",
        min_length=1,
        max_length=100,
    )

    environment: Literal["development", "test", "production"] = "development"

    jwt_secret: SecretStr = Field(
        min_length=32,
    )

    access_token_minutes: int = Field(
        default=15,
        gt=0,
    )

    refresh_token_days: int = Field(
        default=7,
        gt=0,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
