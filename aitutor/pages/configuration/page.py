"""Configuration page to configure the website."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_role_or_permission
from aitutor.models import UserRole
from aitutor.pages.configuration import components
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_admin import with_admin_navbar


@page_require_role_or_permission(required_role=UserRole.ADMIN)
@with_navbar(routes.ADMIN_SETTINGS)
@with_admin_navbar(routes.CONFIGURATION)
def configuration_page() -> rx.Component:
    """Configuration page."""
    return rx.center(
        rx.vstack(
            components.config_form(),
            components.lecturer_registration_token_management(),
            spacing="5",
        ),
        margin_top="2em",
        margin_bottom="2em",
        width="100%",
    )
