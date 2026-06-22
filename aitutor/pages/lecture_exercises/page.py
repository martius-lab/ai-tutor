"""The page to show the existing exercises."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_role_or_permission
from aitutor.models import UserRole
from aitutor.pages.lecture_exercises.components import filter_options, render_exercises
from aitutor.pages.lecture_exercises.state import LectureExercisesState
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_specific_lecture import with_specific_lecture_navbar
from aitutor.utilities.filtering_components import search_badges, search_bar


@page_require_role_or_permission(required_role=UserRole.STUDENT)
@with_navbar(routes.LECTURES)
@with_specific_lecture_navbar("exercises", LectureExercisesState.route_lecture_id)
def lecture_exercises_page() -> rx.Component:
    """Default wrapper for lecture-specific exercises page"""
    return rx.center(
        rx.vstack(
            rx.hstack(
                rx.icon(tag="clock"),
                rx.moment(
                    format="HH:mm:ss",
                    interval=1000,
                    on_change=LectureExercisesState.update_time_left_strings,
                ),
            ),
            rx.vstack(
                search_bar(LectureExercisesState),
                rx.cond(
                    LectureExercisesState.search_values.length() > 0,  # type: ignore
                    search_badges(LectureExercisesState),
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
                        align="center",
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
