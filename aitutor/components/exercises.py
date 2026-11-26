"""Shared components regarding exercises."""

from datetime import datetime

import reflex as rx

import aitutor.global_vars as gv
from aitutor.language_state import LanguageState


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
    next_deadline_task: tuple[str, datetime] | None,
) -> rx.Component:
    """Render brief overview of the exercise status.

    Contains number of open exercises and a progress bar, showing how many have been
    completed already.  Further the title and deadline of the next due exercise is
    shown.

    Args:
        headline: The headline to display above the progress bar.
        num_total_exercises: The total number of exercises.
        num_completed_exercises: The number of completed exercises.
        next_deadline_task: The title and deadline of the next due exercise, or None if
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
                next_deadline_task != None,
                rx.text(
                    next_deadline_task[0],  # type: ignore
                    " — ",
                    rx.moment(
                        date=next_deadline_task[1],  # type: ignore
                        format=gv.MOMENT_DEADLINE_FORMAT,
                        tz=gv.TIME_ZONE,
                    ),
                ),
                rx.text(LanguageState.no_upcoming_deadlines),
            ),
        ),
        spacing="4",
        align="start",
        width="100%",
    )
