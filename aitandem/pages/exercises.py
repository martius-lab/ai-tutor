"""Display different exercises for teachers
to view and add new exercises."""

import reflex as rx
from sqlmodel import select
from aitandem.models import Exercise
from typing import List


class ExercisesState(rx.State):
    """State for managing exercises."""

    exercises: List[Exercise] = []
    has_exercises: bool = False
    has_tags: bool = False

    def on_mount(self):
        """
        Automatically fetch exercises when page loads
        """
        self.fetch_exercises()

    def fetch_exercises(self):
        """
        Fetch exercises from database
        """
        with rx.session() as session:
            exercises = session.exec(
                select(Exercise)
            ).all()  # select all exercises from database
            self.exercises = exercises
            self.has_exercises = len(exercises) > 0  # check if exercises exist
            self.has_tags = any(
                len(exercise.tags) > 0 for exercise in exercises
            )  # check if tags exist


def render_exercise_card(exercise: Exercise) -> rx.Component:
    """Render exercises as cards"""
    return rx.card(  # create a card for each exercise
        rx.vstack(
            rx.heading(exercise.title, size="4"),  # display title
            rx.cond(  # display description if it exists
                exercise.description is not None,
                rx.text(f"Description: {exercise.description}", size="2"),
            ),
            rx.cond(  # display tags if they exist
                ExercisesState.has_tags,
                rx.hstack(
                    rx.text("Tags:", weight="bold"),
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
            "No exercises found. Click 'Add' to create your first exercise!",
            color="gray",
            size="4",
        ),
    )


def exercises() -> rx.Component:
    """Exercises page for teachers"""
    return rx.container(
        rx.vstack(
            rx.heading("Your Exercises:", size="9"),  # page title
            rx.text(
                "Add new exercises by clicking 'Add'! ",
                size="5",
            ),
            render_exercises(),
            rx.center(
                rx.button(  # add button
                    "Add",
                    color_scheme="green",
                    # redirect to add-exercise page when available
                    # on_click=lambda: rx.redirect("/add-exercise", replace=True),
                    width="full",
                ),
                width="100%",
            ),
            spacing="5",
            justify="center",
            min_height="85vh",
        ),
    )


def exercises_default() -> rx.Component:
    """Default wrapper for exercises page"""
    return exercises()
