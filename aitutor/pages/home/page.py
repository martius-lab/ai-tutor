"""This module contains the home page and related components."""

import reflex as rx

from aitutor import routes
from aitutor.pages.navbar import with_navbar
from aitutor.pages.home.components import (
    dashboard_card,
    info_accordion,
    legal_info_links,
)


@with_navbar(routes.HOME)
def home_page() -> rx.Component:
    """Render the homepage with dashboard and info texts."""

    return rx.center(
        rx.vstack(
            # Dashboard Card
            dashboard_card(),
            info_accordion(),
            legal_info_links(),
            width="100%",
            align="center",
            justify="center",
        ),
        margin_top="2em",
        margin_bottom="2em",
        width="90%",
    )
