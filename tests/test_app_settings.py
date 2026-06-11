from pathlib import Path

import pytest
from pydantic_settings import SettingsConfigDict

from aitutor.app_settings import AppSettings


def make_settings(env_file: Path | None) -> AppSettings:
    """Create settings with a test-controlled dotenv source."""

    class TestSettings(AppSettings):
        model_config = SettingsConfigDict(
            env_file=env_file,
            env_file_encoding="utf-8",
            extra="ignore",
        )

    return TestSettings()


def test_app_settings_reads_openai_api_key_from_env(monkeypatch):
    """OPENAI_API_KEY can come from the real process environment."""
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")

    assert make_settings(env_file=None).require_openai_api_key() == "env-key"


def test_app_settings_reads_openai_api_key_from_dotenv(tmp_path, monkeypatch):
    """OPENAI_API_KEY can come from a dotenv file."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_API_KEY=dotenv-key\nOTHER_VALUE=ignored\n")

    assert make_settings(env_file=env_file).require_openai_api_key() == "dotenv-key"


def test_app_settings_requires_openai_api_key(monkeypatch):
    """Missing OPENAI_API_KEY raises a clear configuration error."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        make_settings(env_file=None).require_openai_api_key()
