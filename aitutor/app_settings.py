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
    domain: Annotated[str, StringConstraints(strip_whitespace=True)] = Field(
        default="localhost", validation_alias="DOMAIN"
    )
    smtp_host: Annotated[str, StringConstraints(strip_whitespace=True)] | None = Field(
        default=None, validation_alias="SMTP_HOST"
    )
    smtp_port: int | None = Field(default=None, validation_alias="SMTP_PORT")
    smtp_from_email: Annotated[str, StringConstraints(strip_whitespace=True)] | None = (
        Field(
            default=None,
            validation_alias="SMTP_FROM_EMAIL",
        )
    )
    smtp_username: Annotated[str, StringConstraints(strip_whitespace=True)] | None = (
        Field(
            default=None,
            validation_alias="SMTP_USERNAME",
        )
    )
    smtp_password: str | None = Field(default=None, validation_alias="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=False, validation_alias="SMTP_USE_TLS")
    smtp_use_ssl: bool = Field(default=False, validation_alias="SMTP_USE_SSL")
    smtp_timeout: int = Field(default=10, validation_alias="SMTP_TIMEOUT")

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
