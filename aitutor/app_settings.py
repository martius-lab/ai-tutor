"""Environment-backed application settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE_PATH = Path(__file__).resolve().parent.parent / ".env"


class AppSettings(BaseSettings):
    """Settings loaded from environment variables and the project `.env` file."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="", validation_alias="OPENAI_BASE_URL")

    def require_openai_api_key(self) -> str:
        """Return the configured OpenAI API key or raise a clear startup error."""
        api_key = self.openai_api_key.strip()
        if api_key == "":
            raise ValueError("OPENAI_API_KEY is not set in the environment variables.")
        return api_key

    def optional_openai_base_url(self) -> str | None:
        """Return a configured OpenAI-compatible base URL, if present."""
        base_url = self.openai_base_url.strip()
        return base_url or None


@lru_cache
def get_settings() -> AppSettings:
    """Return cached app settings."""
    return AppSettings()
