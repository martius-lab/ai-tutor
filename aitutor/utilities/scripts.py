"""Utility functions that may be used in standalone scripts."""

import os
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy import Engine
    from sqlmodel import Session


def create_read_only_engine(db_url: str) -> Engine:
    """Create an engine for ``db_url`` that rejects all writes.

    Raises:
        ValueError: If the database backend is not supported.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.engine import make_url

    url = make_url(db_url)
    if url.get_backend_name() == "sqlite":
        if not url.database or url.database == ":memory:":
            raise ValueError("In-memory SQLite databases are not supported.")
        url = url.set(
            database=f"file:{url.database}",
            query={**url.query, "mode": "ro", "uri": "true"},
        )
        return create_engine(url)
    if url.get_backend_name() == "postgresql":
        return create_engine(
            url, connect_args={"options": "-c default_transaction_read_only=on"}
        )
    raise ValueError(f"Unsupported database backend '{url.get_backend_name()}'.")


def connect_database(
    db_url_override: str | None = None, read_only: bool = True
) -> Callable[[], Session]:
    """Connect to the database.

    Args:
        db_url_override: If provided, this database URL will be used instead of the one
            configured in reflex' config.
        read_only: If True, the returned session will be read-only (only supports SQLite
            and PostgreSQL).

    Returns:
        Function that creates a SQLModel session connected to the database.
    """

    if db_url_override:
        # Reflex' config can be overwritten via environment variables.  This needs to
        # happen before reflex is imported below.
        os.environ["REFLEX_DB_URL"] = db_url_override

    # Imported here, so the REFLEX_DB_URL override above is picked up and the script
    # can print its help without loading the (slow) reflex imports.
    import reflex as rx

    # If we don't need a read-only session, we can simply use rx.session, which is
    # configured automatically.
    if not read_only:
        return rx.session

    # Otherwise, we get the database URL from reflex' config and create a read-only
    # session.
    from sqlmodel import Session

    db_url = rx.config.get_config().db_url
    if not db_url:
        raise ValueError("No database URL configured.")
    return lambda: Session(create_read_only_engine(db_url))
