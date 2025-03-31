"""Reflex configuration."""

import reflex as rx

config = rx.Config(
    app_name="aitutor",
    db_url="sqlite:///reflex.db",
    watch_ignore_patterns=[
        ".venv/*",
        ".git/*",
        "alembic/*",
        "build/*",
        "dist/*",
        "*.pyc",
        "__pycache__/*",
    ],
)
