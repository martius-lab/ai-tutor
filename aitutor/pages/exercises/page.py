"""The page to show the existing exercises."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_role_at_least
from aitutor.models import UserRole
from aitutor.pages.exercises.components import filter_options, render_exercises
from aitutor.pages.exercises.state import ExercisesState
from aitutor.pages.navbar import with_navbar
from aitutor.utilities.filtering_components import search_badges, search_bar


@with_navbar(routes.EXERCISES)
@page_require_role_at_least(UserRole.STUDENT)
def exercises_page() -> rx.Component:
    """Default wrapper for exercises page"""
    return rx.center(
        rx.vstack(
            rx.hstack(
                rx.icon(tag="clock"),
                rx.moment(
                    format="HH:mm:ss",
                    interval=1000,
                    on_change=ExercisesState.update_time_left_strings,
                ),
            ),
            rx.vstack(
                search_bar(ExercisesState),
                rx.cond(
                    ExercisesState.search_values.length() > 0,  # type: ignore
                    search_badges(ExercisesState),
                ),
                rx.desktop_only(
                    rx.hstack(
                        filter_options(),
                        spacing="9",
                    ),
                ),
                rx.mobile_and_tablet(
                    rx.vstack(
                        filter_options(),
                    ),
                ),
                align="center",
                justify="center",
            ),
            render_exercises(),
            spacing="5",
            justify="center",
            align="center",
            width="100%",
        ),
        margin_top="2em",
        margin_bottom="2em",
        width="90%",
    )
