from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from reflex_base.utils.serializers import serialize

from aitutor.global_vars import TIME_ZONE
from aitutor.models import BetaExercise


def _naive_local_now() -> datetime:
    return datetime.now(ZoneInfo(TIME_ZONE)).replace(tzinfo=None)


def test_naive_deadline_is_interpreted_in_local_time_zone():
    upcoming = BetaExercise(
        lecture_id=1, deadline=_naive_local_now() + timedelta(minutes=30)
    )
    passed = BetaExercise(
        lecture_id=1, deadline=_naive_local_now() - timedelta(minutes=30)
    )

    assert not upcoming.deadline_exceeded
    assert passed.deadline_exceeded


def test_aware_deadline_in_other_time_zone_is_not_shifted():
    # Replacing the tzinfo would read this UTC time as local time and move the
    # deadline one or two hours into the past.
    deadline = datetime.now(UTC) + timedelta(minutes=30)
    exercise = BetaExercise(lecture_id=1, deadline=deadline, days_to_complete=1)

    assert not exercise.deadline_exceeded


def test_aware_start_in_other_time_zone_is_not_shifted():
    deadline = datetime.now(UTC) + timedelta(days=1, minutes=30)
    exercise = BetaExercise(lecture_id=1, deadline=deadline, days_to_complete=1)

    assert not exercise.is_started


def test_editing_start_is_deadline_minus_days_to_complete():
    deadline = _naive_local_now()
    exercise = BetaExercise(lecture_id=1, deadline=deadline, days_to_complete=7)

    assert exercise.editing_start == deadline - timedelta(days=7)


def test_exercise_without_deadline_has_no_editing_period_and_is_started():
    exercise = BetaExercise(lecture_id=1)

    assert exercise.editing_start is None
    assert exercise.is_started
    assert not exercise.deadline_exceeded


def test_computed_fields_are_sent_to_the_frontend():
    # The manage exercises page reads these values directly from the exercise.
    exercise = BetaExercise(
        lecture_id=1, deadline=_naive_local_now(), days_to_complete=7
    )

    serialized = serialize(exercise)

    assert isinstance(serialized, dict)
    assert {"editing_start", "is_started", "deadline_exceeded"} <= serialized.keys()
