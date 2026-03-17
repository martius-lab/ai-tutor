"""Configuration page to configure the website."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_role_or_permission
from aitutor.models import UserRole
from aitutor.pages.configuration.components import config_form
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_admin import with_admin_navbar


@with_navbar(routes.ADMIN_SETTINGS)
@with_admin_navbar(routes.CONFIGURATION)
@page_require_role_or_permission(required_role=UserRole.OWNER)
def configuration_page() -> rx.Component:
    """Configuration page."""
    return rx.center(
        config_form(),
        margin_top="2em",
        margin_bottom="2em",
        width="100%",
    )
