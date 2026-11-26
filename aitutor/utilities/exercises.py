"""Shared utility functions regarding exercises."""

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from aitutor.global_vars import TIME_ZONE
from aitutor.models import Exercise, ExerciseResult
from aitutor.utilities.helper_functions import to_tz_aware

ExerciseWithMaybeResult = tuple[Exercise, ExerciseResult | None]


@dataclass
class ExerciseWithDeadline:
    """Bundles the data needed to show the exercise with the next deadline."""

    id: int
    title: str
    deadline: datetime


def is_submitted(result: ExerciseResult | None) -> bool:
    """Check if an exercise result has been submitted."""
    return result is not None and result.submit_time_stamp is not None


def not_none[T](value: T | None) -> T:
    """Assert that a value is not None."""
    assert value is not None
    return value


def next_due_exercise(
    exercises_with_result: list[ExerciseWithMaybeResult],
) -> ExerciseWithDeadline | None:
    """Get title and deadline of the task that is due next."""
    time_now = datetime.now(ZoneInfo(TIME_ZONE))

    tasks = [
        ExerciseWithDeadline(not_none(ex.id), ex.title, to_tz_aware(ex.deadline))
        for ex, res in exercises_with_result
        if ex.deadline and to_tz_aware(ex.deadline) > time_now and not is_submitted(res)
    ]

    if not tasks:
        return None

    return min(tasks, key=lambda t: t.deadline)
