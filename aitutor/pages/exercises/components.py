"""Components for the exercises page."""

import reflex as rx

from aitutor.models import Exercise, ExerciseResult
from aitutor.pages.exercises.state import ExercisesState, ExerciseWithResult
from aitutor.utilities.helper_functions import truncate_text_reflex_var


def render_exercise_card(exercise_with_res: ExerciseWithResult) -> rx.Component:
    """Render exercises as cards"""
    exercise: Exercise = exercise_with_res[0]
    result: ExerciseResult | None = exercise_with_res[1]
    is_submitted = result is not None and result.finished_conversation.length() > 0  # type: ignore
    return rx.hstack(
        rx.card(  # create a card for each exercise
            rx.hstack(
                rx.vstack(
                    rx.heading(exercise.title, size="6"),  # display title
                    rx.hstack(
                        rx.text("Description:", weight="bold", size="2"),
                        rx.text(
                            truncate_text_reflex_var(
                                exercise.description, max_length=150
                            ),
                            color="gray",
                            size="2",
                        ),
                        align_items="center",
                        align="center",
                    ),
                    rx.hstack(
                        rx.text("Deadline:", weight="bold", size="2"),
                        rx.text(
                            ExercisesState.deadline_strings[exercise.id],  # type: ignore
                            color="gray",
                            size="2",
                        ),
                    ),
                    rx.cond(
                        exercise.deadline,
                        rx.hstack(
                            rx.text("Time left:", weight="bold", size="2"),
                            rx.text(
                                ExercisesState.time_left_strings[exercise.id],  # type: ignore
                                color="gray",
                                size="2",
                            ),
                            align="center",
                        ),
                    ),
                    rx.cond(  # display tags if they exist
                        exercise.tags.length() > 0,  # type: ignore
                        rx.hstack(
                            rx.text("Tags:", weight="bold", size="2"),
                            rx.hstack(
                                rx.foreach(
                                    exercise.tags,
                                    lambda tag: rx.badge(
                                        tag.name, variant="soft", color_scheme="blue"
                                    ),
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
                                color="green",
                            ),
                            rx.text(
                                "Last submit: "
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


def render_exercises() -> rx.Component:
    """Render the list of exercises"""
    return rx.cond(
        ExercisesState.exercises_with_result.length() > 0,  # type: ignore
        rx.vstack(
            rx.foreach(
                ExercisesState.exercises_with_result,
                render_exercise_card,
            ),
            spacing="4",
            width="100%",
        ),
        rx.text(  # if no exercises exist
            "There exist no exercises yet.",
            color="gray",
            size="4",
            text_align="center",
            width="100%",
        ),
    )
