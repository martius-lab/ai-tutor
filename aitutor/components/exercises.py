"""Shared components regarding exercises."""

import reflex as rx

import aitutor.global_vars as gv
from aitutor import routes
from aitutor.language_state import LanguageState
from aitutor.utilities.exercises import ExerciseWithDeadline


def compute_progress_value(
    num_total_exercises: int, num_completed_exercises: int
) -> rx.vars.Var[int | float]:
    """Compute the progress value (0-100) for the progress bar."""
    return rx.cond(
        num_total_exercises > 0,
        num_completed_exercises / num_total_exercises * 100,
        100,
    )


def exercise_status_overview(
    *,
    headline: str | rx.vars.StringVar[str],
    num_total_exercises: int,
    num_completed_exercises: int,
    next_due_exercise: ExerciseWithDeadline | None,
) -> rx.Component:
    """Render brief overview of the exercise status.

    Contains number of open exercises and a progress bar, showing how many have been
    completed already.  Further the title and deadline of the next due exercise is
    shown.

    Args:
        headline: The headline to display above the progress bar.
        num_total_exercises: The total number of exercises.
        num_completed_exercises: The number of completed exercises.
        next_due_exercise: The title and deadline of the next due exercise, or None if
            there is no upcoming exercise.
    """
    progress_value = compute_progress_value(
        num_total_exercises, num_completed_exercises
    )
    return rx.vstack(
        rx.heading(headline),
        rx.progress(value=progress_value, max=100, width="100%"),  # type: ignore
        rx.hstack(
            rx.icon("circle-check", color=gv.GREEN_CHECK_COLOR, size=20),
            rx.cond(
                num_total_exercises > 0,
                rx.text(
                    f"{num_completed_exercises} / {num_total_exercises}"
                    f" {LanguageState.open_exercises_submitted}"
                ),
                rx.text(LanguageState.no_pending_exercises),
            ),
            align="center",
        ),
        rx.hstack(
            rx.text(LanguageState.next_deadline, weight="bold"),
            rx.cond(
                next_due_exercise != None,
                rx.link(
                    rx.text(
                        next_due_exercise.title,  # type: ignore
                        " — ",
                        rx.moment(
                            date=next_due_exercise.deadline,  # type: ignore
                            format=gv.MOMENT_DEADLINE_FORMAT,
                            tz=gv.TIME_ZONE,
                        ),
                    ),
                    href=f"{routes.CHAT}/{next_due_exercise.id}",  # type: ignore
                ),
                rx.text(LanguageState.no_upcoming_deadlines),
            ),
        ),
        spacing="4",
        align="start",
        width="100%",
    )
