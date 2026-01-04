"""Admin settings page."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_role_at_least
from aitutor.language_state import LanguageState as LS
from aitutor.models import UserRole
from aitutor.pages.navbar import with_navbar

# (link text, route, icon)
setting_pages = [
    (LS.manage_exercises_link, routes.MANAGE_EXERCISES, "pencil-line"),
    (LS.manage_users, routes.MANAGE_USERS, "users"),
    (LS.configuration, routes.CONFIGURATION, "file-sliders"),
    (LS.reports, routes.REPORTS, "flag"),
]


@with_navbar(routes.ADMIN_SETTINGS)
@page_require_role_at_least(UserRole.ADMIN)
def admin_settings_page() -> rx.Component:
    """admin settings page."""
    return rx.box(
        rx.vstack(
            rx.foreach(
                setting_pages,
                lambda setting_page: rx.card(
                    rx.hstack(
                        rx.icon(
                            setting_page[2],
                        ),
                        rx.heading(setting_page[0], size="3"),
                        justify="center",
                    ),
                    on_click=rx.redirect(setting_page[1]),
                    _hover={"cursor": "pointer"},
                    padding="1em",
                    width="100%",
                    align="center",
                    justify="center",
                ),
            ),
            width="40em",
            max_width="100%",
            padding="4",
        ),
        display="flex",
        justify_content="center",
        margin_top="2em",
        margin_bottom="2em",
        width="90%",
    )
