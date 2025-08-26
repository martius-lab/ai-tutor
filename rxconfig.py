"""Reflex configuration."""

import reflex as rx

config = rx.Config(
    app_name="aitutor",
    db_url="sqlite:///reflex.db",
    plugins=[rx.plugins.SitemapPlugin()],
    telemetry_enabled=False,
    show_built_with_reflex=False,
)
