"""Reflex configuration."""

import reflex as rx
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    """Database settings loaded from environment variables or `.env` file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    POSTGRES_PASSWORD: str = ""


db_settings = PostgresSettings()
db_url = f"postgresql+psycopg://postgres:{db_settings.POSTGRES_PASSWORD}@localhost:5454/postgres"

config = rx.Config(
    app_name="aitutor",
    db_url=db_url,
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.RadixThemesPlugin(
            theme=rx.theme(
                accent_color="indigo",
                gray_color="slate",
                radius="medium",
            )
        ),
    ],
    telemetry_enabled=False,
    show_built_with_reflex=False,
)
