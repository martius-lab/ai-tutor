"""Displays the submitted chat messages"""

import reflex as rx
from aitutor.auth.protection import require_role_at_least
from aitutor.pages.navbar import with_navbar
from aitutor.models import UserRole


@with_navbar
@require_role_at_least(UserRole.STUDENT)
def finished_view_default() -> rx.Component:
    """Renders the web page."""
    return rx.container(
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.heading(
                        "Exercise: ",
                        size="5",
                    ),
                    rx.icon(
                        "circle-check",
                        color="green",
                    ),
                    align="center",
                    justify="between",
                    width="100%",
                ),
                spacing="5",
                justify="start",
                min_height="85vh",
                max_height="85vh",
                height="100%",
            ),
            width="100%",
        ),
        align_items="center",
        width="100%",
    )
