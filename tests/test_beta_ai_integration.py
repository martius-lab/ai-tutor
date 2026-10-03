"""Regression tests for the shared Classic and Level AI exercise views."""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import Mock
from zoneinfo import ZoneInfo

import pytest

from aitutor import routes
from aitutor.global_vars import TIME_ZONE
from aitutor.pages.home.state import HomeExerciseCard, HomeState
from aitutor.pages.lecture_exercises.state import ExerciseCard, LectureExercisesState
from aitutor.utilities.helper_functions import deadline_sort_key


@pytest.mark.parametrize(
    "deadline,expected",
    [
        (None, datetime.max.replace(tzinfo=ZoneInfo(TIME_ZONE))),
        (
            datetime(2026, 1, 1, 12, tzinfo=UTC).replace(tzinfo=None),
            datetime(2026, 1, 1, 12, tzinfo=ZoneInfo(TIME_ZONE)),
        ),
        (
            datetime(2026, 1, 1, 12, tzinfo=UTC),
            datetime(2026, 1, 1, 12, tzinfo=UTC),
        ),
    ],
)
def test_shared_deadline_sorting_keeps_original_normalization(deadline, expected):
    assert deadline_sort_key(deadline) == expected
    assert deadline_sort_key(deadline).tzinfo == ZoneInfo(TIME_ZONE)


def exercise_card(*, beta: bool, overdue: bool, submitted: bool) -> ExerciseCard:
    return ExerciseCard(
        id=1,
        title="Exercise",
        description="Description",
        deadline=datetime(2026, 1, 1, 12, tzinfo=UTC),
        deadline_exceeded=overdue,
        is_hidden=False,
        is_beta=beta,
        is_submitted=submitted,
        submit_time_stamp="",
        tags=[],
        chat_route=f"{routes.BETA_AI_CHAT}/2/1" if beta else f"{routes.CHAT}/1",
    )


@pytest.mark.parametrize("beta", [False, True])
def test_expired_exercises_keep_chat_routes_and_existing_filters(beta):
    card = exercise_card(beta=beta, overdue=True, submitted=False)
    state = Mock(
        spec=LectureExercisesState,
        exercise_cards=[card],
        show_closed_exercises=True,
        show_submitted_exercises=True,
    )
    LectureExercisesState._fill_exercise_groups(state)
    assert state.closed_deadline_exercises == [card]
    assert card.chat_route == (
        f"{routes.BETA_AI_CHAT}/2/1" if beta else f"{routes.CHAT}/1"
    )
    state.show_closed_exercises = False
    LectureExercisesState._fill_exercise_groups(state)
    assert state.closed_deadline_exercises == []


def test_home_counts_submitted_cards_from_both_ai_types():
    # Reflex's internal initialization flag is absent from its generated signature.
    init_kwargs: dict[str, Any] = {"_reflex_internal_init": True}
    state = HomeState(**init_kwargs)
    state.exercise_cards = [
        HomeExerciseCard("Classic", None, False, True, f"{routes.CHAT}/1"),
        HomeExerciseCard("Level", None, True, True, f"{routes.BETA_AI_CHAT}/2/1"),
        HomeExerciseCard("Open", None, True, False, f"{routes.BETA_AI_CHAT}/2/2"),
    ]
    assert state.completed_exercises_num == 2
    assert state.progress_value == 66
