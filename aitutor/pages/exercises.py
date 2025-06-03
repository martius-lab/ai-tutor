"""Display different exercises for teachers
to view and add new exercises."""

import reflex as rx
from sqlmodel import select

from aitutor.models import Exercise
from aitutor.pages.navbar import with_navbar
from aitutor.auth.protection import require_role_at_least
from aitutor.models import UserRole, ExerciseResult
from aitutor.auth.state import SessionState
from aitutor.pages.chat import TIME_FORMAT

from typing import Optional

ExerciseWithResult = tuple[Exercise, Optional[ExerciseResult]]


class ExercisesState(SessionState):
    """State for managing exercises."""

    has_exercises: bool = False
    has_tags: bool = False
    exercises_with_result: list[ExerciseWithResult] = []

    @rx.event
    def fetch_exercises(self):
        """
        Fetch exercises from database
        """
        with rx.session() as session:
            stmt = select(Exercise, ExerciseResult).join(ExerciseResult, isouter=True)
            exercises_with_result = session.exec(stmt).all()
            self.has_exercises = len(exercises_with_result) > 0
            self.has_tags = any(
                len(exercise.tags) > 0 for exercise, _ in exercises_with_result
            )
            self.exercises_with_result = [(x[0], x[1]) for x in exercises_with_result]

    @rx.var
    def submit_time_stamps(self) -> dict[int, str]:
        """
        Dictionary to store submit time stamps for exercises.
        Key: Exercise ID, Value: Submit Time as string.
        """
        return {
            exercise_with_res[0].id: (
                exercise_with_res[1].submit_time_stamp.strftime(TIME_FORMAT)
                if exercise_with_res[1] is not None
                and exercise_with_res[1].submit_time_stamp is not None
                else ""
            )
            for exercise_with_res in self.exercises_with_result
            if exercise_with_res[0].id is not None
        }


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


def exercises() -> rx.Component:
    """Exercises page for teachers"""
    return rx.container(
        rx.vstack(
            rx.heading("Exercises:", size="9"),  # page title
            render_exercises(),
            spacing="5",
            justify="center",
            min_height="85vh",
            align="center",
        ),
    )


@with_navbar
@require_role_at_least(UserRole.STUDENT)
def exercises_default() -> rx.Component:
    """Default wrapper for exercises page"""
    return exercises()
