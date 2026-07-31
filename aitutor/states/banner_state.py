# ruff: noqa: D102, B018
"""State management for global announcement banners."""

from typing import Literal

import reflex as rx

from aitutor.auth.state import SessionState
from aitutor.config import get_config
from aitutor.models import BannerMessageType

BannerColor = Literal["blue", "amber", "red", "green"]

BANNER_TYPE_COLORS: dict[BannerMessageType, BannerColor] = {
    BannerMessageType.INFO: "blue",
    BannerMessageType.WARNING: "amber",
    BannerMessageType.ERROR: "red",
    BannerMessageType.SUCCESS: "green",
}

BannerIcon = Literal["info", "triangle-alert", "circle-alert", "check-circle-2"]

BANNER_TYPE_ICONS: dict[BannerMessageType, BannerIcon] = {
    BannerMessageType.INFO: "info",
    BannerMessageType.WARNING: "triangle-alert",
    BannerMessageType.ERROR: "circle-alert",
    BannerMessageType.SUCCESS: "check-circle-2",
}


class BannerState(SessionState):
    """Global state for site-wide announcement banner."""

    trigger_var: bool = False

    @rx.var(initial_value="")
    def message(self) -> str:
        self.trigger_var
        try:
            return get_config().banner_message
        except Exception:
            return ""

    @rx.var(initial_value=BannerMessageType.INFO)
    def message_type(self) -> BannerMessageType:
        self.trigger_var
        try:
            return get_config().banner_message_type
        except Exception:
            return BannerMessageType.INFO

    @rx.var(initial_value=False)
    def is_open(self) -> bool:
        self.trigger_var
        try:
            return get_config().banner_is_open
        except Exception:
            return False

    @rx.event
    def refresh_banner(self):
        """Refresh the banner vars by toggling the trigger_var."""
        self.trigger_var = not self.trigger_var

    @rx.var
    def color_scheme(self) -> BannerColor:
        """Return the corresponding color scheme for the message type."""
        return BANNER_TYPE_COLORS.get(self.message_type, "blue")

    @rx.var
    def icon(self) -> BannerIcon:
        """Return the corresponding icon name for the message type."""
        return BANNER_TYPE_ICONS.get(self.message_type, "info")
