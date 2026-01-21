"""Reflex configuration."""

import reflex as rx
from sqlalchemy import event
from sqlalchemy.engine import Engine


# Enable foreign key constraints for SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key constraints on SQLite connections."""
    # Check if this is a SQLite connection (sqlite3 or pysqlite2)
    module_name = dbapi_conn.__class__.__module__
    if module_name.startswith("sqlite3") or module_name.startswith("pysqlite"):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


config = rx.Config(
    app_name="aitutor",
    db_url="sqlite:///reflex.db",
    plugins=[rx.plugins.SitemapPlugin()],
    telemetry_enabled=False,
    show_built_with_reflex=False,
)
