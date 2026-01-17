"""Admin settings navbar"""

import reflex as rx

import aitutor.routes as routes
from aitutor.language_state import LanguageState

admin_links = [
    (LanguageState.manage_exercises_link, routes.MANAGE_EXERCISES, "book-copy"),
    (LanguageState.manage_prompts, routes.PROMPTS, "text-search"),
    (LanguageState.manage_users, routes.MANAGE_USERS, "users"),
    (LanguageState.reports, routes.REPORTS, "flag"),
    (LanguageState.configuration, routes.CONFIGURATION, "file-sliders"),
]


def tab_content(link):
    """
    The Icon and text for a tab in the admin navbar.

    This function is needed because the icon for some reason loads slower than the text,
    causing a layout shift. By wrapping them in a box with fixed dimensions, this can
    be avoided. You will still see a "flash" when switching tabs, because icons are not
    loaded from the start, but at least the layout will not shift.
    """
    return (
        rx.hstack(
            rx.box(
                rx.icon(link[2], size=20),
                width="20px",
                height="20px",
                display="flex",
                align_items="center",
                justify_content="center",
                flex_shrink=0,
            ),
            rx.text(link[0]),
            spacing="2",
            align="center",
        ),
    )


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
                        tab_content(link),
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
