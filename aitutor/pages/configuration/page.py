"""Configuration page to configure the website."""

import reflex as rx


from aitutor import routes
from aitutor.models import UserRole
from aitutor.pages.navbar import with_navbar
from aitutor.auth.protection import page_require_role_at_least
from aitutor.pages.configuration.components import config_form


@with_navbar(routes.CONFIGURATION)
@page_require_role_at_least(UserRole.ADMIN)
def configuration_page() -> rx.Component:
    """Configuration page."""
    return rx.center(
        rx.vstack(
            config_form(),
            spacing="3",
            align="center",
            justify="center",
        ),
        margin_top="2em",
        margin_bottom="2em",
        width="90%",
    )
