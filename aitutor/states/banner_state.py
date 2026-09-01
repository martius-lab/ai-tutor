# ruff: noqa: D102, B018
"""State management for global announcement banners."""

from typing import Literal

import reflex as rx

from aitutor.auth.state import SessionState
from aitutor.config import get_config
from aitutor.models import BannerMessageType

BannerColor = Literal["blue", "amber", "red", "green"]

INITIAL_BANNER_MESSAGE: str = ""
INITIAL_BANNER_MESSAGE_TYPE: BannerMessageType = BannerMessageType.INFO
INITIAL_BANNER_IS_OPEN: bool = False


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

    @rx.var(initial_value=INITIAL_BANNER_MESSAGE)
    def message(self) -> str:
        self.trigger_var
        return get_config().banner_message

    @rx.var(initial_value=INITIAL_BANNER_MESSAGE_TYPE)
    def message_type(self) -> BannerMessageType:
        self.trigger_var
        return get_config().banner_message_type

    @rx.var(initial_value=INITIAL_BANNER_IS_OPEN)
    def is_open(self) -> bool:
        self.trigger_var
        return get_config().banner_is_open

    @rx.event
    def refresh_banner(self):
        """Refresh the banner vars by toggling the trigger_var."""
        self.trigger_var = not self.trigger_var

    @rx.var(initial_value=BANNER_TYPE_COLORS[INITIAL_BANNER_MESSAGE_TYPE])
    def color_scheme(self) -> BannerColor:
        """Return the corresponding color scheme for the message type."""
        return BANNER_TYPE_COLORS[self.message_type]

    @rx.var(initial_value=BANNER_TYPE_ICONS[INITIAL_BANNER_MESSAGE_TYPE])
    def icon(self) -> BannerIcon:
        """Return the corresponding icon name for the message type."""
        return BANNER_TYPE_ICONS[self.message_type]
