"""Environment-backed application settings."""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, StringConstraints, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Settings loaded from environment variables and the project `.env` file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1)
    ] = Field(validation_alias="OPENAI_API_KEY")
    openai_base_url: str | None = Field(
        default=None, validation_alias="OPENAI_BASE_URL"
    )

    @field_validator("openai_base_url", mode="before")
    @classmethod
    def _empty_openai_base_url_as_none(cls, value: object) -> object:
        """Treat an empty optional base URL as unset."""
        if isinstance(value, str) and value.strip() == "":
            return None
        return value


@lru_cache
def get_settings() -> AppSettings:
    """Return cached app settings."""
    return AppSettings()  # pyright: ignore[reportCallIssue]
