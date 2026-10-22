from pathlib import Path

import pytest
from pydantic import ValidationError

from reelshelf.core.config import Settings


def test_settings_load_values_from_dotenv(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "REELSHELF_APP_NAME=ReelShelf Test API\n"
        "REELSHELF_ENVIRONMENT=test\n"
        f"REELSHELF_JWT_SECRET={'x' * 48}\n"
        "REELSHELF_ACCESS_TOKEN_MINUTES=20\n",
        encoding="utf-8",
    )

    settings = Settings()

    assert settings.app_name == "ReelShelf Test API"
    assert settings.environment == "test"
    assert settings.access_token_minutes == 20
    assert settings.refresh_token_days == 7
    assert settings.jwt_secret.get_secret_value() == "x" * 48


def test_environment_variables_override_dotenv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        f"REELSHELF_JWT_SECRET={'x' * 48}\nREELSHELF_ACCESS_TOKEN_MINUTES=15\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("REELSHELF_ACCESS_TOKEN_MINUTES", "30")

    settings = Settings()

    assert settings.access_token_minutes == 30


def test_settings_require_jwt_secret() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings()

    errors = exc_info.value.errors()

    assert any(
        error["loc"] == ("jwt_secret",) and error["type"] == "missing"
        for error in errors
    )


@pytest.mark.parametrize(
    ("variable", "value", "field"),
    [
        ("REELSHELF_JWT_SECRET", "short", "jwt_secret"),
        ("REELSHELF_ACCESS_TOKEN_MINUTES", "0", "access_token_minutes"),
        ("REELSHELF_REFRESH_TOKEN_DAYS", "-1", "refresh_token_days"),
        ("REELSHELF_ENVIRONMENT", "unknown", "environment"),
    ],
)
def test_settings_reject_invalid_values(
    monkeypatch: pytest.MonkeyPatch,
    variable: str,
    value: str,
    field: str,
) -> None:
    monkeypatch.setenv("REELSHELF_JWT_SECRET", "x" * 48)
    monkeypatch.setenv(variable, value)

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    assert any(error["loc"] == (field,) for error in exc_info.value.errors())


def test_settings_hide_secret_in_repr(settings: Settings) -> None:
    assert settings.jwt_secret.get_secret_value() not in repr(settings)


def test_settings_reject_unknown_dotenv_keys(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        f"REELSHELF_JWT_SECRET={'x' * 48}\nREELSHELF_UNKNOWN_OPTION=true\n",
        encoding="utf-8",
    )

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    assert any(error["type"] == "extra_forbidden" for error in exc_info.value.errors())
