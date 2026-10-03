"""small functions to help"""

from datetime import datetime
from zoneinfo import ZoneInfo

import reflex as rx

from aitutor.global_vars import TIME_ZONE


def deadline_sort_key(deadline: datetime | None) -> datetime:
    """Compare stored (naive) and timezone-aware deadlines consistently."""
    if deadline is None:
        return datetime.max.replace(tzinfo=ZoneInfo(TIME_ZONE))
    if deadline.tzinfo is None:
        return deadline.replace(tzinfo=ZoneInfo(TIME_ZONE))
    return deadline.astimezone(ZoneInfo(TIME_ZONE))


def truncate_text_reflex_var(text, max_length=100):
    """Truncate text to a maximum length with ellipsis."""
    return rx.cond(
        text.length() > max_length,
        text[:max_length] + "...",
        text,
    )
