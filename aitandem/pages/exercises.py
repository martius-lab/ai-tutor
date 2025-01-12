"""Display different exercises for teachers
to view and add new exercises."""

import reflex as rx
from sqlmodel import select
from aitandem.models import Exercise
from typing import List, Optional

def fetch_exercises(session_id: Optional[str] = None) -> List[Exercise]:
    """
    Fetch exercises from the database
    """
    with rx.session() as session:
        exercises = session.exec(select(Exercise)).all()
        return exercises
    
def render_exercise_card(exercise: Exercise) -> rx.Component:
    """Render exercises as cards"""
    return rx.card(
        rx.vstack(
            rx.heading(exercise.title, size="4"),
            rx.cond(
                exercise.description is not None,
                rx.text(f"Description: {exercise.description}", size="2")
            ),
            rx.cond(
                len(exercise.tags) > 0,
                rx.hstack(
                    rx.text("Tags:", weight="bold"),
                    rx.hstack(
                        *[
                            rx.badge(tag, variant="soft", color_scheme="blue") 
                            for tag in exercise.tags
                        ],
                        spacing="2"
                    )
                )
            ),
            rx.cond(
                exercise.image is not None,
                rx.image(
                    src=exercise.image,
                    width="200px",
                    height="auto",
                    border_radius="md"
                )
            ),
            spacing="2",
            align="start",
        ),
        variant="surface",
        width="100%",
    )

def render_exercises() -> rx.Component:
    """Render the list of exercises"""
    exercises = fetch_exercises()
    return rx.cond(
        len(exercises) > 0,
        rx.vstack(
            *[render_exercise_card(exercise) for exercise in exercises],
            spacing="4",
            width="100%"
        ),
        rx.text(
            "No exercises found. Click 'Add' to create your first exercise!", 
            color="gray", 
            size="4"
        )
    )

def exercises() -> rx.Component:
    """Exercises page for teachers"""
    return rx.container(
        rx.vstack(
            rx.heading("Your Exercises:", size="9"),
            rx.text(
                "Add new exercises by clicking 'Add'! ",
                size="5",
            ),
            render_exercises(),
            rx.center(
                rx.button(
                    "Add",
                    color_scheme="green",
                    #on_click=lambda: rx.redirect("/add-exercise", replace=True), #redirect to add-exercise page when available
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