"""Components for the exercises page."""

import reflex as rx

from aitutor.models import Exercise
from aitutor.models import ExerciseResult
from aitutor.pages.exercises.state import ExercisesState, ExerciseWithResult


def render_exercise_card(exercise_with_res: ExerciseWithResult) -> rx.Component:
    """Render exercises as cards"""
    exercise: Exercise = exercise_with_res[0]
    result: ExerciseResult | None = exercise_with_res[1]
    is_submitted = result is not None and result.finished_conversation.length() > 0  # type: ignore
    return rx.card(  # create a card for each exercise
        rx.hstack(
            rx.vstack(
                rx.heading(exercise.title, size="6"),  # display title
                rx.cond(  # display description if it exists
                    exercise.description is not None,
                    rx.hstack(
                        rx.text("Description:", weight="bold", size="2"),
                        rx.text(exercise.description, color="gray", size="2"),
                        align_items="center",
                        align="center",
                    ),
                ),
                rx.cond(  # display tags if they exist
                    ExercisesState.has_tags,
                    rx.hstack(
                        rx.text("Tags:", weight="bold", size="2"),
                        rx.hstack(
                            rx.foreach(
                                exercise.tags,
                                lambda tag: rx.badge(
                                    tag, variant="soft", color_scheme="blue"
                                ),
                            ),
                            spacing="2",
                        ),
                    ),
                ),
                rx.cond(  # display image if it exists
                    exercise.image is not None,
                    rx.image(
                        src=exercise.image,
                        width="200px",
                        height="auto",
                        border_radius="md",
                    ),
                ),
                rx.cond(
                    is_submitted,
                    rx.text(
                        "Last submit: "
                        + ExercisesState.submit_time_stamps[exercise.id],
                        color_scheme="green",
                        size="2",
                    ),
                ),
                spacing="2",
                align="start",
            ),
            rx.cond(
                is_submitted,
                rx.icon(
                    "circle-check",
                    color="green",
                    size=30,
                ),
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
    )


def render_exercises() -> rx.Component:
    """Render the list of exercises"""
    return rx.cond(
        ExercisesState.has_exercises,  # if they exist
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
