"""Main navbar and app shell layout."""

from typing import Optional

import reflex as rx

import aitutor.routes as routes
from aitutor import DisplayConfigState
from aitutor.language_state import LanguageState
from aitutor.pages.navbar_links import (
    get_links,
    navbar_link_desktop,
    navbar_link_mobile,
)
from aitutor.pages.navbar_profile import profile_menu, profile_menu_actions


def navbar(route_to_highlight: Optional[str]) -> rx.Component:
    """
    Creates the default navigation bar component for the application.

    Args:
        route_to_highlight (str): The route that identifies which link to highlight
        in the navbar.

    Returns:
        rx.Component: A Reflex box component containing the navigation bar.
    """
    return rx.box(
        rx.desktop_only(
            rx.hstack(
                rx.hstack(
                    rx.image(
                        src="/logo.jpg",
                        width="2.25em",
                        height="auto",
                        border_radius="25%",
                        on_click=rx.redirect(routes.HOME),
                        cursor="pointer",
                    ),
                    rx.heading("AI Tutor", size="7", weight="bold"),
                    align_items="center",
                ),
                rx.vstack(
                    rx.text(DisplayConfigState.course_name, weight="bold"),
                    rx.hstack(
                        rx.foreach(
                            get_links(),
                            lambda link: rx.cond(
                                link != None,
                                navbar_link_desktop(link, route_to_highlight),
                            ),
                        ),
                        spacing="5",
                        align="center",
                        wrap="wrap",
                    ),
                    align="center",
                ),
                rx.hstack(
                    rx.color_mode.button(),
                    profile_menu(),
                ),
                justify="between",
                align_items="center",
            ),
        ),
        rx.mobile_and_tablet(
            rx.hstack(
                rx.hstack(
                    rx.image(
                        src="/logo.jpg",
                        width="2em",
                        height="auto",
                        border_radius="25%",
                        on_click=rx.redirect(routes.HOME),
                        cursor="pointer",
                    ),
                    rx.heading("AI Tutor", size="6", weight="bold"),
                    align_items="center",
                ),
                rx.menu.root(
                    rx.menu.trigger(
                        rx.icon_button(
                            rx.icon("menu", size=22),
                            variant="soft",
                            radius="full",
                            class_name="mobile-menu-trigger",
                        ),
                    ),
                    rx.menu.content(
                        rx.box(
                            rx.text(
                                DisplayConfigState.course_name,
                                color_scheme="gray",
                                weight="bold",
                            ),
                            padding="0.5em",
                        ),
                        rx.separator(),
                        rx.foreach(
                            get_links(),
                            lambda link: rx.cond(
                                link != None,
                                navbar_link_mobile(link, route_to_highlight),
                            ),
                        ),
                        rx.separator(),
                        profile_menu_actions(),
                        min_width="14rem",
                        max_width="90vw",
                    ),
                ),
                justify="between",
                align_items="center",
                width="100%",
            ),
        ),
        class_name="site-navbar",
        padding="1em",
        width="100%",
    )


def site_footer() -> rx.Component:
    """Render legal links at the bottom of the app shell."""
    return rx.hstack(
        rx.mobile_and_tablet(rx.color_mode.button()),
        rx.link(LanguageState.impressum, href=routes.IMPRESSUM),
        rx.link(LanguageState.privacy_notice, href=routes.PRIVACY_NOTICE),
        justify="center",
        align="center",
        spacing="5",
        padding="1rem",
        class_name="site-footer",
    )


def with_navbar(route_to_highlight: Optional[str] = None):
    """
    Decorator to add a navigation bar to a component.

    Args:
        route_to_highlight (str): The route that identifies which link to highlight
        in the navbar.
    """

    def decorator(
        component_factory: rx.app.ComponentCallable,
    ) -> rx.app.ComponentCallable:
        """
        Decorator to add a navigation bar to a component.

        Args:
            component_factory (rx.app.ComponentCallable):
            A callable that returns a Reflex component.

        Returns:
            rx.app.ComponentCallable:
            A callable that returns a Reflex component with the navigation bar.
        """
        return lambda: rx.flex(
            navbar(route_to_highlight),
            rx.box(
                component_factory(),
                class_name="app-main",
            ),
            site_footer(),
            direction="column",
            spacing="0",
            padding="0",
            align="center",
            class_name="app-shell",
        )

    return decorator
