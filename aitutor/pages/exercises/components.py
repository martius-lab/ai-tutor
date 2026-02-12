"""Components for the exercises page."""

import reflex as rx

import aitutor.global_vars as gv
from aitutor.language_state import LanguageState
from aitutor.models import Exercise, ExerciseResult
from aitutor.pages.exercises.state import ExercisesState, ExerciseWithResult
from aitutor.utilities.helper_functions import truncate_text_reflex_var


def filter_options() -> rx.Component:
    """Show filter options"""
    return rx.fragment(
        rx.hstack(
            rx.icon("circle-check", size=20),
            rx.text(LanguageState.show_submitted_exercises),
            rx.checkbox(
                checked=ExercisesState.show_submitted_exercises,
                on_change=ExercisesState.toggle_show_submitted_exercises,
            ),
            align="center",
            justify="center",
        ),
        rx.hstack(
            rx.icon("timer_off", size=20),
            rx.text(LanguageState.show_closed_exercises),
            rx.checkbox(
                checked=ExercisesState.show_closed_exercises,
                on_change=ExercisesState.toggle_show_closed_exercises,
            ),
            align="center",
            justify="center",
        ),
    )


def render_exercise_card(exercise_with_res: ExerciseWithResult) -> rx.Component:
    """Render exercises as cards"""
    exercise: Exercise = exercise_with_res[0]
    result: ExerciseResult | None = exercise_with_res[1]
    is_submitted = result is not None and result.finished_conversation.length() > 0  # type: ignore
    return rx.hstack(
        rx.card(  # create a card for each exercise
            rx.hstack(
                rx.vstack(
                    rx.heading(exercise.title, size="6"),
                    rx.text(
                        truncate_text_reflex_var(exercise.description, max_length=150),
                        size="2",
                    ),
                    rx.cond(
                        exercise.deadline,
                        rx.hstack(
                            rx.icon("calendar-clock", size=20),
                            rx.text(LanguageState.deadline, weight="bold", size="2"),
                            rx.text(
                                ExercisesState.deadline_strings[exercise.id],  # type: ignore
                                size="2",
                            ),
                        ),
                    ),
                    rx.cond(
                        exercise.deadline,
                        rx.hstack(
                            rx.icon("hourglass", size=20),
                            rx.text(LanguageState.time_left, weight="bold", size="2"),
                            rx.text(
                                rx.cond(
                                    ExercisesState.time_left_strings[exercise.id],  # type: ignore
                                    ExercisesState.time_left_strings[exercise.id],  # type: ignore
                                    LanguageState.deadline_has_passed,
                                ),
                                size="2",
                            ),
                            align="center",
                        ),
                    ),
                    rx.cond(  # display tags if they exist
                        exercise.tags.length() > 0,  # type: ignore
                        rx.hstack(
                            rx.icon("tag", size=20),
                            rx.hstack(
                                rx.foreach(
                                    exercise.tags,
                                    lambda tag: rx.badge(tag.name, variant="soft"),
                                ),
                                spacing="2",
                                wrap="wrap",
                            ),
                        ),
                    ),
                    rx.cond(
                        is_submitted,
                        rx.hstack(
                            rx.icon(
                                "circle-check",
                                color=gv.GREEN_CHECK_COLOR,
                                size=20,
                            ),
                            rx.text(
                                LanguageState.last_submit
                                + ExercisesState.submit_time_stamps[exercise.id],
                                color_scheme="green",
                                size="2",
                            ),
                            align="center",
                        ),
                    ),
                    spacing="2",
                    align="start",
                ),
                align="center",
                justify="between",
            ),
            variant="surface",
            width="100%",
            on_click=rx.redirect(
                f"/chat/{exercise.id}",
            ),
            _hover={"cursor": "pointer"},
            style=rx.cond(
                exercise_with_res[0].is_hidden,
                {"opacity": "0.5"},
                {"opacity": "1"},
            ),
        ),
        align="center",
        justify="center",
        width="100%",
    )


def exercises_seperator(title) -> rx.Component:
    """Render a separator with a title"""
    return rx.hstack(
        rx.divider(),
        rx.heading(title, size="5", align="center", white_space="nowrap"),
        rx.divider(),
        width="100%",
        align="center",
        spacing="4",
    )


def render_exercises() -> rx.Component:
    """Render the list of exercises"""
    return rx.vstack(
        rx.cond(
            ExercisesState.open_deadline_exercises.length() > 0,  # type: ignore
            rx.vstack(
                exercises_seperator(LanguageState.open_deadline),
                rx.foreach(
                    ExercisesState.open_deadline_exercises,
                    render_exercise_card,
                ),
                spacing="4",
                width="100%",
            ),
        ),
        rx.cond(
            ExercisesState.no_deadline_exercises.length() > 0,  # type: ignore
            rx.vstack(
                exercises_seperator(LanguageState.no_deadline),
                rx.foreach(
                    ExercisesState.no_deadline_exercises,
                    render_exercise_card,
                ),
                spacing="4",
                width="100%",
            ),
        ),
        rx.cond(
            ExercisesState.closed_deadline_exercises.length() > 0,  # type: ignore
            rx.vstack(
                exercises_seperator(LanguageState.closed_deadline),
                rx.foreach(
                    ExercisesState.closed_deadline_exercises,
                    render_exercise_card,
                ),
                spacing="4",
                width="100%",
            ),
        ),
        rx.cond(
            ExercisesState.exercises_with_result.length() == 0,  # type: ignore
            rx.callout(LanguageState.no_exercises_available, icon="info"),
        ),
        align="center",
        spacing="4",
        width="100%",
    )
