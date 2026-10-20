from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from aitutor.global_vars import TIME_ZONE
from aitutor.models import BetaExercise


def _naive_local_now() -> datetime:
    return datetime.now(ZoneInfo(TIME_ZONE)).replace(tzinfo=None)


def test_naive_deadline_is_interpreted_in_local_time_zone():
    upcoming = BetaExercise(deadline=_naive_local_now() + timedelta(minutes=30))
    passed = BetaExercise(deadline=_naive_local_now() - timedelta(minutes=30))

    assert not upcoming.deadline_exceeded
    assert passed.deadline_exceeded


def test_aware_deadline_in_other_time_zone_is_not_shifted():
    # Replacing the tzinfo would read this UTC time as local time and move the
    # deadline one or two hours into the past.
    deadline = datetime.now(UTC) + timedelta(minutes=30)
    exercise = BetaExercise(deadline=deadline, days_to_complete=1)

    assert not exercise.deadline_exceeded


def test_aware_start_in_other_time_zone_is_not_shifted():
    deadline = datetime.now(UTC) + timedelta(days=1, minutes=30)
    exercise = BetaExercise(deadline=deadline, days_to_complete=1)

    assert not exercise.is_started
