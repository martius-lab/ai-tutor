"""Components for the Beta AI student exercise list page."""

import reflex as rx

import aitutor.routes as routes
from aitutor.models import BetaExercise
from aitutor.pages.beta_ai_student_exercises.state import BetaAIStudentExercisesState


def student_exercises_header() -> rx.Component:
    """Render the page header."""
    return rx.vstack(
        rx.heading("Beta AI Student Exercises", size="7"),
        rx.text(
            "Choose a Beta AI exercise and open the chat.",
            color_scheme="gray",
        ),
        align="start",
        spacing="1",
        width="100%",
    )


def beta_exercise_card(exercise: BetaExercise) -> rx.Component:
    """Render one visible Beta AI exercise for students."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading(exercise.title, size="4"),
                rx.spacer(),
                rx.badge("Beta", color_scheme="purple"),
                width="100%",
                align="center",
            ),
            rx.hstack(
                rx.button(
                    rx.icon("message-circle"),
                    "Open Chat",
                    variant="soft",
                    on_click=rx.redirect(routes.BETA_AI_CHAT + f"/{exercise.id}"),
                    _hover={"cursor": "pointer"},
                ),
                justify="end",
                width="100%",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        width="100%",
    )


def beta_ai_student_exercises_content() -> rx.Component:
    """Render the full Beta AI student exercise list content."""
    return rx.vstack(
        student_exercises_header(),
        rx.cond(
            BetaAIStudentExercisesState.beta_exercises.length() == 0,  # type: ignore
            rx.callout(
                "No visible Beta AI exercises are available yet.",
                icon="info",
                width="100%",
            ),
            rx.vstack(
                rx.foreach(
                    BetaAIStudentExercisesState.beta_exercises,
                    beta_exercise_card,
                ),
                spacing="3",
                width="100%",
            ),
        ),
        spacing="4",
        width="100%",
    )
