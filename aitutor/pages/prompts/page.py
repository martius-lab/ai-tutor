"""Prompts page to configure the prompts."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_role_at_least
from aitutor.models import UserRole
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_admin import with_admin_navbar
from aitutor.pages.prompts.components import prompt_management


@with_navbar(routes.ADMIN_SETTINGS)
@with_admin_navbar(routes.PROMPTS)
@page_require_role_at_least(UserRole.ADMIN)
def prompts_page() -> rx.Component:
    """Prompts page."""
    return rx.center(
        prompt_management(),
        margin_top="2em",
        margin_bottom="2em",
        width="100%",
    )
