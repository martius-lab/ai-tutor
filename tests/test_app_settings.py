from pathlib import Path

import pytest
from pydantic import ValidationError
from pydantic_settings import SettingsConfigDict

from aitutor.app_settings import AppSettings


def make_settings(env_file: str | Path | None) -> AppSettings:
    """Create settings with a test-controlled dotenv source."""

    class TestSettings(AppSettings):
        model_config = SettingsConfigDict(
            env_file=env_file,
            env_file_encoding="utf-8",
            extra="ignore",
        )

    return TestSettings()  # pyright: ignore[reportCallIssue]


def test_app_settings_reads_openai_api_key_from_env(monkeypatch):
    """OPENAI_API_KEY can come from the real process environment."""
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")

    assert make_settings(env_file=None).openai_api_key == "env-key"


def test_app_settings_reads_openai_api_key_from_cwd_dotenv(tmp_path, monkeypatch):
    """OPENAI_API_KEY can come from the current working directory dotenv file."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)
    Path(".env").write_text("OPENAI_API_KEY=dotenv-key\nOTHER_VALUE=ignored\n")

    assert make_settings(env_file=".env").openai_api_key == "dotenv-key"


def test_app_settings_requires_openai_api_key(monkeypatch):
    """Missing OPENAI_API_KEY raises a clear configuration error."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValidationError, match="OPENAI_API_KEY"):
        make_settings(env_file=None)


def test_app_settings_rejects_empty_openai_api_key(monkeypatch):
    """OPENAI_API_KEY cannot be empty."""
    monkeypatch.setenv("OPENAI_API_KEY", " ")

    with pytest.raises(ValidationError):
        make_settings(env_file=None)


def test_app_settings_reads_optional_openai_base_url(tmp_path, monkeypatch):
    """OPENAI_BASE_URL can come from a dotenv file when configured."""
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_BASE_URL=https://example.test/v1\n")

    assert make_settings(env_file=env_file).openai_base_url == "https://example.test/v1"


def test_app_settings_defaults_openai_base_url_to_none(monkeypatch):
    """OPENAI_BASE_URL is optional."""
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    assert make_settings(env_file=None).openai_base_url is None


def test_app_settings_treats_empty_openai_base_url_as_none(monkeypatch):
    """Empty OPENAI_BASE_URL is equivalent to leaving it unset."""
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    monkeypatch.setenv("OPENAI_BASE_URL", " ")

    assert make_settings(env_file=None).openai_base_url is None


def test_app_settings_defaults_optional_smtp_fields_to_none(monkeypatch):
    """Unset optional SMTP strings remain distinguishable from configured values."""
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    for env_var in (
        "SMTP_HOST",
        "SMTP_FROM_EMAIL",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
    ):
        monkeypatch.delenv(env_var, raising=False)

    settings = make_settings(env_file=None)

    assert settings.smtp_host is None
    assert settings.smtp_from_email is None
    assert settings.smtp_username is None
    assert settings.smtp_password is None
