"""Display different exercises for teachers
to view and add new exercises."""

import reflex as rx
from sqlmodel import select
from typing import List

from aitutor.models import Exercise
from aitutor.pages.navbar import with_navbar
from aitutor.auth.protection import require_role_at_least
from aitutor.models import UserRole


class ExercisesState(rx.State):
    """State for managing exercises."""

    exercises: List[Exercise] = []
    has_exercises: bool = False
    has_tags: bool = False

    @rx.event
    def fetch_exercises(self):
        """
        Fetch exercises from database
        """
        with rx.session() as session:
            exercises = session.exec(
                select(Exercise)
            ).all()  # select all exercises from database
            self.exercises = list(exercises)
            self.has_exercises = len(exercises) > 0  # check if exercises exist
            self.has_tags = any(
                len(exercise.tags) > 0 for exercise in exercises
            )  # check if tags exist


def render_exercise_card(exercise: Exercise) -> rx.Component:
    """Render exercises as cards"""
    return rx.card(  # create a card for each exercise
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
                    src=exercise.image, width="200px", height="auto", border_radius="md"
                ),
            ),
            spacing="2",
            align="start",
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
                ExercisesState.exercises,  # iterate through exercises and render cards
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
        ),
    )


@with_navbar
@require_role_at_least(UserRole.STUDENT)
def exercises_default() -> rx.Component:
    """Default wrapper for exercises page"""
    return exercises()
