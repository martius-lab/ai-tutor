"""
This module defines the navbar components for the Reflex application.
"""

import reflex as rx

links = [
    ("Home", "/"),
    ("Login", "/login"),
    ("Registration", "/register"),
    ("Chat", "/chat"),
    ("Add Exercises", "/add-exercises"),
    ("Exercises", "/exercises"),
]


def navbar_link(text: str, url: str) -> rx.Component:
    """
    Creates a navigation link component.

    Args:
        text (str): The text to display for the link.
        url (str): The URL the link points to.

    Returns:
        rx.Component: A Reflex link component.
    """
    return rx.link(rx.text(text, size="4", weight="medium"), href=url)


def navbar_default() -> rx.Component:
    """
    Creates the default navigation bar component for the application.

    Returns:
        rx.Component: A Reflex box component containing the navigation bar.
    """
    return rx.box(
        rx.desktop_only(
            rx.color_mode.button(position="bottom-left", type="button"),
            rx.hstack(
                rx.hstack(
                    rx.image(
                        src="/logo.jpg",
                        width="2.25em",
                        height="auto",
                        border_radius="25%",
                        on_click=rx.redirect("/"),
                        cursor="pointer",
                    ),
                    rx.heading("AI Tutor", size="7", weight="bold"),
                    align_items="center",
                ),
                rx.hstack(
                    *[navbar_link(text, url) for text, url in links],
                    spacing="5",
                ),
                rx.menu.root(
                    rx.menu.trigger(
                        rx.icon_button(
                            rx.icon("user"),
                            size="2",
                            radius="full",
                        )
                    ),
                    rx.menu.content(
                        rx.menu.item("Log out"),  # TODO: Add log out functionality
                    ),
                    justify="end",
                ),
                justify="between",
                align_items="center",
            ),
        ),
        rx.mobile_and_tablet(
            rx.color_mode.button(position="bottom-left", type="button"),
            rx.hstack(
                rx.hstack(
                    rx.image(
                        src="/logo.jpg",
                        width="2em",
                        height="auto",
                        border_radius="25%",
                    ),
                    rx.heading("AI Tutor", size="6", weight="bold"),
                    align_items="center",
                ),
                rx.hstack(
                    rx.menu.root(
                        rx.menu.trigger(rx.icon("menu", size=30)),
                        rx.menu.content(
                            *[
                                rx.menu.item(rx.link(text, href=url))
                                for text, url in links
                            ]
                        ),
                    ),
                    rx.menu.root(
                        rx.menu.trigger(
                            rx.icon_button(
                                rx.icon("user"),
                                size="2",
                                radius="full",
                            )
                        ),
                        rx.menu.content(
                            rx.menu.item("Log out"),
                        ),
                    ),
                ),
                justify="between",
                align_items="center",
            ),
        ),
        bg=rx.color("accent", 3),
        padding="1em",
        # position="fixed",
        # top="0px",
        # z_index="5",
        width="100%",
    )


def with_navbar(
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
    return lambda: rx.vstack(
        navbar_default(), component_factory(), spacing="0", padding="0", align="center"
    )
