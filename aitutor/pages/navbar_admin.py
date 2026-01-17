"""Admin settings navbar"""

import reflex as rx

import aitutor.routes as routes
from aitutor.language_state import LanguageState

admin_links = [
    (LanguageState.manage_exercises_link, routes.MANAGE_EXERCISES),
    (LanguageState.manage_users, routes.MANAGE_USERS),
    (LanguageState.configuration, routes.CONFIGURATION),
    (LanguageState.reports, routes.REPORTS),
]


def admin_navbar(tab_to_highlight: str) -> rx.Component:
    """
    Create a navigation bar for the admin settings pages.

    Args:
        tab_to_highlight (str): The route that identifies which tab to highlight.
    """
    return rx.box(
        rx.tabs.root(
            rx.tabs.list(
                rx.foreach(
                    admin_links,
                    lambda link: rx.tabs.trigger(
                        link[0],
                        value=link[1],
                        on_click=rx.redirect(link[1]),
                        _hover={"cursor": "pointer"},
                    ),
                ),
                width="100%",
            ),
            default_value=tab_to_highlight,
            width="100%",
        ),
        margin_top="0.5em",
        width="100%",
    )


def with_admin_navbar(tab_to_highlight: str):
    """
    Decorator to add a admin navigation bar to a component.

    Args:
        tab_to_highlight (str): The page that identifies which tab to highlight
        in the navbar.
    """

    def decorator(
        component_factory: rx.app.ComponentCallable,
    ) -> rx.app.ComponentCallable:
        """
        Decorator to add a admin navigation bar to a component.

        Args:
            component_factory (rx.app.ComponentCallable):
            A callable that returns a Reflex component.

        Returns:
            rx.app.ComponentCallable:
            A callable that returns a Reflex component with the admin navigation bar.
        """
        return lambda: rx.vstack(
            admin_navbar(tab_to_highlight),
            component_factory(),
            spacing="0",
            padding="0",
            align="center",
            width="90%",
        )

    return decorator
