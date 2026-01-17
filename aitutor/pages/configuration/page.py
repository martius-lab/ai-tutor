"""Configuration page to configure the website."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_role_at_least
from aitutor.language_state import LanguageState as LS
from aitutor.models import UserRole
from aitutor.pages.configuration.components import config_form, prompt_management
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_admin import with_admin_navbar


@with_navbar(routes.MANAGE_EXERCISES)
@with_admin_navbar(routes.CONFIGURATION)
@page_require_role_at_least(UserRole.ADMIN)
def configuration_page() -> rx.Component:
    """Configuration page."""
    return rx.center(
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger(
                    LS.general_configuration,
                    value="general",
                    _hover={"cursor": "pointer"},
                ),
                rx.tabs.trigger(
                    LS.manage_prompts, value="prompts", _hover={"cursor": "pointer"}
                ),
            ),
            rx.tabs.content(
                rx.vstack(
                    rx.box(height="1em"),
                    config_form(),
                    spacing="5",
                    align="center",
                    justify="center",
                ),
                value="general",
            ),
            rx.tabs.content(
                rx.vstack(
                    rx.box(height="1em"),
                    prompt_management(),
                    spacing="5",
                    align="center",
                    justify="center",
                ),
                value="prompts",
            ),
            default_value="general",
            width="100%",
        ),
        margin_top="1em",
        margin_bottom="2em",
        width="100%",
    )
