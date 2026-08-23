"""The Components for the home page."""

import reflex as rx

import aitutor.global_vars as gv
from aitutor import DisplayConfigState, routes
from aitutor.language_state import LanguageState
from aitutor.models import Exercise, ExerciseResult, Lecture
from aitutor.pages.home.state import ExerciseWithResult, HomeState, LectureExerciseGroup
from aitutor.pages.legal_infos.loader_functions import get_privacy_notice_short
from aitutor.routes import LOGIN, REGISTER


def dashboard_card():
    """Render the dashboard card"""
    exercises_num = HomeState.exercises_with_result.length()  # type: ignore

    return (
        rx.card(
            rx.cond(
                HomeState.is_authenticated,
                # dashboard for logged in users
                rx.vstack(
                    rx.heading(
                        LanguageState.dashboard,
                    ),
                    rx.text(LanguageState.welcome_back, weight="medium"),
                    rx.progress(value=HomeState.progress_value, max=100, width="100%"),  # type: ignore
                    rx.hstack(
                        rx.icon("circle-check", color=gv.GREEN_CHECK_COLOR, size=20),
                        rx.cond(
                            exercises_num > 0,
                            rx.text(
                                f"{HomeState.completed_exercises_num} \
                                /{exercises_num} \
                                    {LanguageState.open_exercises_submitted}"
                            ),
                            rx.text(LanguageState.no_pending_exercises),
                        ),
                        align="center",
                    ),
                    rx.hstack(
                        rx.text(LanguageState.next_deadline, weight="bold"),
                        rx.cond(
                            HomeState.next_deadline_task,
                            rx.text(HomeState.next_deadline_task),
                            rx.text(LanguageState.no_upcoming_deadlines),
                        ),
                    ),
                    spacing="4",
                    align="start",
                    width="100%",
                ),
                # dashboard for not logged in users
                rx.vstack(
                    rx.heading(LanguageState.dashboard),
                    rx.text(
                        LanguageState.welcome_message,
                        weight="medium",
                    ),
                    rx.hstack(
                        rx.button(
                            rx.hstack(
                                rx.icon(
                                    "log-in",
                                    size=15,
                                ),
                                rx.text(
                                    LanguageState.log_in,
                                    size="2",
                                    margin_bottom="6px",
                                    margin_top="6px",
                                ),
                                align="center",
                                justify="center",
                                spacing="1",
                            ),
                            _hover={"cursor": "pointer"},
                            on_click=rx.redirect(LOGIN),
                        ),
                        rx.button(
                            rx.hstack(
                                rx.icon(
                                    "notepad-text",
                                    size=15,
                                ),
                                rx.text(
                                    LanguageState.register,
                                    size="2",
                                    margin_bottom="6px",
                                    margin_top="6px",
                                ),
                                align="center",
                                justify="center",
                                spacing="1",
                            ),
                            _hover={"cursor": "pointer"},
                            color_scheme="green",
                            on_click=rx.redirect(REGISTER),
                        ),
                    ),
                    align="start",
                    width="100%",
                ),
            ),
            width="100%",
            padding="4",
        ),
    )


def global_exercise_card(exercise_with_result: ExerciseWithResult) -> rx.Component:
    """Render one exercise on the global home page."""
    exercise: Exercise = exercise_with_result[0]
    result: ExerciseResult | None = exercise_with_result[1]
    is_submitted = result is not None and result.finished_conversation.length() > 0  # type: ignore

    return rx.card(
        rx.vstack(
            rx.heading(exercise.title, size="4"),
            rx.hstack(
                rx.icon("calendar-clock", size=18),
                rx.text(LanguageState.deadline, weight="bold", size="2"),
                rx.cond(
                    exercise.deadline,
                    rx.text(HomeState.deadline_strings[exercise.id], size="2"),  # type: ignore
                    rx.text(LanguageState.no_deadline, size="2"),
                ),
                align="center",
                wrap="wrap",
            ),
            rx.cond(
                is_submitted,
                rx.hstack(
                    rx.icon("circle-check", color=gv.GREEN_CHECK_COLOR, size=18),
                    rx.text(LanguageState.view_your_submission, size="2"),
                    align="center",
                ),
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        width="100%",
        variant="surface",
        on_click=rx.redirect(f"{routes.CHAT}/{exercise.id}"),
        _hover={"cursor": "pointer"},
    )


def lecture_exercise_group(group: LectureExerciseGroup) -> rx.Component:
    """Render all global-home exercises belonging to one lecture."""
    lecture: Lecture = group[0]
    exercises: list[ExerciseWithResult] = group[1]

    return rx.vstack(
        rx.link(
            rx.heading(lecture.lecture_name, size="5"),
            href=f"{routes.LECTURE_OVERVIEW}/{lecture.id}",
        ),
        rx.foreach(exercises, global_exercise_card),
        spacing="3",
        align="start",
        width="100%",
    )


def global_exercises_overview() -> rx.Component:
    """Render accessible exercises grouped by lecture."""
    return rx.cond(
        HomeState.is_authenticated,
        rx.card(
            rx.vstack(
                rx.heading(LanguageState.exercises_link, size="6"),
                rx.cond(
                    HomeState.lecture_exercise_groups.length() > 0,  # type: ignore
                    rx.vstack(
                        rx.foreach(
                            HomeState.lecture_exercise_groups,
                            lecture_exercise_group,
                        ),
                        spacing="5",
                        width="100%",
                        max_height="26rem",
                        overflow_y="auto",
                        padding_right="2",
                    ),
                    rx.callout(LanguageState.no_exercises_available, icon="info"),
                ),
                spacing="4",
                align="start",
                width="100%",
            ),
            width="100%",
            padding="4",
        ),
    )


def info_accordion():
    """Render the info accordion"""
    privacy_notice_short: str = get_privacy_notice_short()
    return (
        rx.cond(
            (DisplayConfigState.how_to_use_text != "")
            | (DisplayConfigState.general_information_text != "")
            | (privacy_notice_short != ""),
            rx.accordion.root(
                rx.cond(
                    DisplayConfigState.how_to_use_text != "",
                    rx.accordion.item(
                        header=LanguageState.how_to_use_aitutor,
                        content=rx.markdown(DisplayConfigState.how_to_use_text),
                    ),
                ),
                rx.cond(
                    DisplayConfigState.general_information_text != "",
                    rx.accordion.item(
                        header=LanguageState.general_info,
                        content=rx.markdown(
                            DisplayConfigState.general_information_text
                        ),
                    ),
                ),
                rx.cond(
                    privacy_notice_short != "",
                    rx.accordion.item(
                        header=LanguageState.privacy_notice_short,
                        content=rx.markdown(privacy_notice_short),
                    ),
                ),
                width="100%",
                collapsible=True,
                variant="outline",
            ),
        ),
    )
