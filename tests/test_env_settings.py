from pathlib import Path

import pytest
from pydantic import ValidationError
from pydantic_settings import SettingsConfigDict

from aitutor.env_settings import EnvSettings


def make_settings(env_file: str | Path | None) -> EnvSettings:
    """Create settings with a test-controlled dotenv source."""

    class TestSettings(EnvSettings):
        model_config = SettingsConfigDict(
            env_file=env_file,
            env_file_encoding="utf-8",
            extra="ignore",
        )

    return TestSettings()  # pyright: ignore[reportCallIssue]


def test_env_settings_reads_openai_api_key_from_env(monkeypatch):
    """OPENAI_API_KEY can come from the real process environment."""
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")

    assert make_settings(env_file=None).openai_api_key == "env-key"


def test_env_settings_reads_openai_api_key_from_cwd_dotenv(tmp_path, monkeypatch):
    """OPENAI_API_KEY can come from the current working directory dotenv file."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)
    Path(".env").write_text("OPENAI_API_KEY=dotenv-key\nOTHER_VALUE=ignored\n")

    assert make_settings(env_file=".env").openai_api_key == "dotenv-key"


def test_env_settings_requires_openai_api_key(monkeypatch):
    """Missing OPENAI_API_KEY raises a clear configuration error."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValidationError, match="OPENAI_API_KEY"):
        make_settings(env_file=None)


def test_env_settings_rejects_empty_openai_api_key(monkeypatch):
    """OPENAI_API_KEY cannot be empty."""
    monkeypatch.setenv("OPENAI_API_KEY", " ")

    with pytest.raises(ValidationError):
        make_settings(env_file=None)


def test_env_settings_reads_optional_openai_base_url(tmp_path, monkeypatch):
    """OPENAI_BASE_URL can come from a dotenv file when configured."""
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_BASE_URL=https://example.test/v1\n")

    assert make_settings(env_file=env_file).openai_base_url == "https://example.test/v1"


def test_env_settings_defaults_openai_base_url_to_none(monkeypatch):
    """OPENAI_BASE_URL is optional."""
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    assert make_settings(env_file=None).openai_base_url is None


def test_env_settings_treats_empty_openai_base_url_as_none(monkeypatch):
    """Empty OPENAI_BASE_URL is equivalent to leaving it unset."""
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    monkeypatch.setenv("OPENAI_BASE_URL", " ")

    assert make_settings(env_file=None).openai_base_url is None


def test_env_settings_smtp_optional(monkeypatch):
    """If no SMTP values are set, the settings object will be None."""
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    for env_var in (
        "SMTP_HOST",
        "SMTP_FROM_EMAIL",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
        "SMTP_USE_TLS",
        "SMTP_USE_SSL",
    ):
        monkeypatch.delenv(env_var, raising=False)

    settings = make_settings(env_file=None)

    assert settings.SMTP is None


def test_smtp_settings_from_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("SMTP_HOST", "smtpserv.uni-tuebingen.de")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_FROM_EMAIL", "AI Tutor <noreply@example.com>")
    monkeypatch.setenv("SMTP_USERNAME", "smtp-user")
    monkeypatch.setenv("SMTP_PASSWORD", "smtp-password")
    monkeypatch.setenv("SMTP_USE_TLS", "true")
    monkeypatch.setenv("SMTP_USE_SSL", "false")

    settings = make_settings(env_file=None)

    assert settings.SMTP is not None
    assert settings.SMTP.HOST == "smtpserv.uni-tuebingen.de"
    assert settings.SMTP.PORT == 587
    assert settings.SMTP.FROM_EMAIL == "AI Tutor <noreply@example.com>"
    assert settings.SMTP.USERNAME == "smtp-user"
    assert settings.SMTP.PASSWORD == "smtp-password"
    assert settings.SMTP.USE_TLS is True
    assert settings.SMTP.USE_SSL is False


def test_smtp_settings_default_to_no_tls(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_FROM_EMAIL", "noreply@example.com")
    monkeypatch.delenv("SMTP_USE_TLS", raising=False)
    monkeypatch.delenv("SMTP_USE_SSL", raising=False)

    settings = make_settings(env_file=None)

    assert settings.SMTP is not None
    assert settings.SMTP.USE_TLS is False
    assert settings.SMTP.USE_SSL is False


def test_smtp_settings_require_host(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.setenv("SMTP_FROM_EMAIL", "noreply@example.com")

    with pytest.raises(ValidationError, match="HOST"):
        make_settings(env_file=None)


def test_smtp_settings_require_port(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("SMTP_PORT", raising=False)
    monkeypatch.setenv("SMTP_FROM_EMAIL", "noreply@example.com")

    with pytest.raises(ValidationError, match="PORT"):
        make_settings(env_file=None)


def test_smtp_settings_require_from_email(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("SMTP_FROM_EMAIL", raising=False)
    monkeypatch.setenv("SMTP_HOST", "smtp@example.com")

    with pytest.raises(ValidationError, match="FROM_EMAIL"):
        make_settings(env_file=None)


def test_smtp_settings_reject_partial_credentials(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "123")
    monkeypatch.setenv("SMTP_FROM_EMAIL", "noreply@example.com")
    monkeypatch.setenv("SMTP_USERNAME", "foobar")

    with pytest.raises(ValidationError, match="SMTP_PASSWORD"):
        make_settings(env_file=None)
