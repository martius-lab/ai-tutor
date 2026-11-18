"""small functions to help"""

from datetime import datetime
from zoneinfo import ZoneInfo

import reflex as rx

from aitutor.global_vars import TIME_ZONE


def truncate_text_reflex_var(text, max_length=100):
    """Truncate text to a maximum length with ellipsis."""
    return rx.cond(
        text.length() > max_length,
        text[:max_length] + "...",
        text,
    )


def to_tz_aware(value: datetime) -> datetime:
    """
    Make a datetime read from the database timezone-aware.

    Sqlite does not store the time zone and thus gives us a naive datetime, which is in
    TIME_ZONE because that is what was written.  Postgres does store it and gives us an
    aware datetime, which must be left alone.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=ZoneInfo(TIME_ZONE))
    return value
