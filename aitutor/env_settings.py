"""Environment-backed application settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import (
    BaseModel,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class SmtpSettings(BaseModel):
    """Settings for SMTP email sending."""

    HOST: str
    PORT: int
    FROM_EMAIL: str

    USERNAME: str | None = Field(default=None)
    PASSWORD: str | None = Field(default=None)

    USE_TLS: bool = Field(default=False)
    USE_SSL: bool = Field(default=False)

    TIMEOUT: int = Field(default=10)

    @field_validator("PORT", "TIMEOUT", mode="after")
    @classmethod
    def _validate_greater_than_zero(cls, value: int) -> int:
        """Validate that the value is greater than zero."""
        if value <= 0:
            raise ValueError("must be greater than zero")
        return value

    @model_validator(mode="after")
    def _validate_tls_ssl(self) -> SmtpSettings:
        """Validate that TLS and SSL are not both enabled."""
        if self.USE_TLS and self.USE_SSL:
            raise ValueError("SMTP_USE_TLS and SMTP_USE_SSL cannot both be enabled.")
        return self

    @model_validator(mode="after")
    def _validate_username_password(self) -> SmtpSettings:
        """Validate that username and password are both set or both unset."""
        if bool(self.USERNAME) != bool(self.PASSWORD):
            raise ValueError(
                "SMTP_USERNAME and SMTP_PASSWORD must be configured together."
            )
        return self


class EnvSettings(BaseSettings):
    """Settings loaded from environment variables and the project `.env` file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="_",
        env_nested_max_split=1,
        extra="ignore",
    )

    OPENAI_API_KEY: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1)
    ]
    OPENAI_BASE_URL: str | None = Field(default=None)
    DOMAIN: str = Field(default="localhost")

    SMTP: SmtpSettings | None = None

    @field_validator("OPENAI_BASE_URL", mode="before")
    @classmethod
    def _empty_openai_base_url_as_none(cls, value: object) -> object:
        """Treat an empty optional base URL as unset."""
        if isinstance(value, str) and value.strip() == "":
            return None
        return value


@lru_cache
def get_env_settings() -> EnvSettings:
    """Return cached app settings."""
    return EnvSettings()  # pyright: ignore[reportCallIssue]
