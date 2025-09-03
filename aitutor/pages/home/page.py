"""This module contains the home page and related components."""

import reflex as rx

from aitutor.pages.navbar import with_navbar
from aitutor.pages.home.components import dashboard_card, info_accordion


@with_navbar
def home_page() -> rx.Component:
    """Render the homepage with dashboard and info texts."""

    return rx.center(
        rx.vstack(
            # Dashboard Card
            dashboard_card(),
            info_accordion(),
            width="100%",
            align="center",
            justify="center",
        ),
        margin_top="2em",
        margin_bottom="2em",
        width="90%",
    )
