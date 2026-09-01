"""Announcement banner component for displaying site-wide notices."""

import reflex as rx

from aitutor.states.banner_state import BannerState


def announcement_banner() -> rx.Component:
    """Render a site-wide announcement banner when a message is set."""
    return rx.cond(
        BannerState.is_open & (BannerState.message != ""),
        rx.box(
            rx.callout.root(
                rx.callout.icon(rx.icon(BannerState.icon, size=18)),
                rx.markdown(
                    BannerState.message,
                    component_map={
                        "p": lambda text: rx.text(text, margin="0", size="2")
                    },
                ),
                color_scheme=BannerState.color_scheme,
                variant="soft",
                size="1",
            ),
            width="100%",
            padding_x="1em",
            margin_y="1em",
        ),
    )
