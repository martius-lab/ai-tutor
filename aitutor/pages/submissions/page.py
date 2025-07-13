"""Page for the teacher to see submissions."""

import reflex as rx

from aitutor.models import UserRole
from aitutor.pages.submissions.state import SubmissionsState
from aitutor.pages.navbar import with_navbar
from aitutor.auth.protection import page_require_role_at_least
from aitutor.pages.submissions.components import submissions_table, search_badges


@with_navbar
@page_require_role_at_least(UserRole.TEACHER)
def submissions_page() -> rx.Component:
    """Manage exercises page."""
    return rx.center(
        rx.vstack(
            rx.heading(
                "Submissions",
                size="8",
                padding_top="1em",
                padding_bottom="0.5em",
                align="center",
            ),
            rx.form.root(
                rx.hstack(
                    rx.input(
                        rx.input.slot(rx.icon("search")),
                        name="search_value",
                        placeholder="Search...",
                        required=True,
                        value=SubmissionsState.current_search_value,
                        on_change=SubmissionsState.search_with_value,
                    ),
                    rx.button(
                        rx.icon("plus"),
                        _hover={"cursor": "pointer"},
                    ),
                ),
                on_submit=SubmissionsState.add_search_value,
                reset_on_submit=True,
                max_width="250px",
            ),
            search_badges(),
            submissions_table(),
            align="center",
            justify="center",
        ),
    )
