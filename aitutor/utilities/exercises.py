"""Shared utility functions regarding exercises."""

from datetime import datetime
from zoneinfo import ZoneInfo

from aitutor.global_vars import TIME_ZONE
from aitutor.models import Exercise, ExerciseResult
from aitutor.utilities.helper_functions import to_tz_aware

ExerciseWithMaybeResult = tuple[Exercise, ExerciseResult | None]


def is_submitted(result: ExerciseResult | None) -> bool:
    """Check if an exercise result has been submitted."""
    return result is not None and result.submit_time_stamp is not None


def next_deadline_task(
    exercises_with_result: list[ExerciseWithMaybeResult],
) -> tuple[str, datetime] | None:
    """Get title and deadline of the task that is due next."""
    time_now = datetime.now(ZoneInfo(TIME_ZONE))

    tasks = [
        (ex.title, to_tz_aware(ex.deadline))
        for ex, res in exercises_with_result
        if ex.deadline and to_tz_aware(ex.deadline) > time_now and not is_submitted(res)
    ]

    if not tasks:
        return None

    return min(tasks, key=lambda t: t[1])
