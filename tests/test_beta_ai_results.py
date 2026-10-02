"""Regression tests for Level AI snapshots, evaluations and token summaries."""

import inspect
from contextlib import contextmanager
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from sqlmodel import Session, SQLModel, create_engine

from aitutor.models import (
    BetaExercise,
    BetaExerciseResult,
    GlobalPermission,
    LectureRole,
    LinkUserLecture,
)
from aitutor.pages.beta_ai_finished_view import state as finished
from aitutor.pages.beta_ai_finished_view_tutor import state as tutor_finished
from aitutor.pages.beta_ai_finished_view_tutor.evaluations import evaluated_messages
from aitutor.pages.beta_ai_trace_logs import state as trace_state
from aitutor.pages.beta_ai_trace_logs.state import BetaAITraceLogsState
from aitutor.pages.lecture_token_analyzer.state import LectureTokenAnalyzerState


def test_withdrawal_preserves_conversation_and_learning_progress():
    result = BetaExerciseResult(
        userinfo_id=1,
        beta_exercise_id=2,
        conversation_text=[{"role": "student", "content": "Latest answer"}],
        finished_conversation=[{"role": "student", "content": "Submitted answer"}],
        submit_time_stamp=datetime.now(UTC),
        tokens_used=123,
        analysis_allowed=True,
        completed_at=datetime.now(UTC),
    )
    before = result.model_dump()
    finished.withdraw_beta_submission(result)
    assert result.model_dump() == {
        **before,
        "finished_conversation": [],
        "submit_time_stamp": None,
    }


@pytest.mark.parametrize("lecture_id,user_id", [(None, 1), (2, None), (2, 1)])
def test_finished_view_access_uses_existing_permission_helper(
    monkeypatch, lecture_id, user_id
):
    check = Mock(return_value=True)
    monkeypatch.setattr(finished, "user_may_view_lecture", check)
    state = Mock(
        spec=finished.BetaAIFinishedViewState,
        authenticated_user=SimpleNamespace(id=user_id),
        global_permissions=[],
    )
    session = Mock()
    allowed = finished.BetaAIFinishedViewState._user_may_view_exercise(
        state, session, BetaExercise(title="Test", lecture_id=lecture_id)
    )
    valid = lecture_id is not None and user_id is not None
    assert allowed is valid
    if valid:
        check.assert_called_once_with(
            session, user_id=user_id, global_permissions=[], lecture_id=lecture_id
        )
    else:
        check.assert_not_called()


def test_evaluations_match_snapshot_answers_and_stop_at_later_traces():
    conversation = [
        {"role": "tutor", "content": "Question"},
        {"role": "student", "content": "Failed request"},
        {"role": "student", "content": "Answer"},
        {"role": "tutor", "content": "Follow-up"},
        {"role": "student", "content": "Answer"},
    ]
    session = Mock()
    session.exec.return_value.all.return_value = [
        SimpleNamespace(
            student_answer="Answer",
            trace_entry={"final_pattern": "correct_but_incomplete"},
        ),
        SimpleNamespace(
            student_answer="Answer",
            trace_entry={"final_pattern": "sufficient_for_completion"},
        ),
        SimpleNamespace(
            student_answer="Later unsubmitted answer",
            trace_entry={"final_pattern": "off_task"},
        ),
    ]
    result = BetaExerciseResult(id=1, userinfo_id=1, beta_exercise_id=2)
    messages = evaluated_messages(session, result, conversation)
    assert [(m.role, m.content) for m in messages] == [
        (item["role"], item["content"]) for item in conversation
    ]
    assert messages[1].badges == []
    assert messages[2].badges == [{"label": "Correct, incomplete", "color": "blue"}]
    assert messages[4].badges == [{"label": "Sufficient", "color": "green"}]


def test_evaluations_without_result_leave_snapshot_unchanged():
    session = Mock()
    messages = evaluated_messages(
        session, None, [{"role": "student", "content": "Answer"}]
    )
    assert messages[0].content == "Answer"
    assert messages[0].badges == []
    session.exec.assert_not_called()


def test_tutor_finished_view_reuses_queried_result_and_submitted_snapshot(monkeypatch):
    result = BetaExerciseResult(
        id=1,
        userinfo_id=2,
        beta_exercise_id=3,
        finished_conversation=[{"role": "student", "content": "Submitted"}],
        conversation_text=[{"role": "student", "content": "Later answer"}],
    )
    session = Mock()
    session.exec.return_value.one_or_none.return_value = (
        BetaExercise(id=3, title="Test", lecture_id=4),
        "Student",
        result,
    )

    @contextmanager
    def session_context():
        yield session

    monkeypatch.setattr(tutor_finished.rx, "session", session_context)
    evaluate = Mock(return_value=[])
    monkeypatch.setattr(tutor_finished, "evaluated_messages", evaluate)
    state = Mock(
        spec=tutor_finished.BetaAIFinishedViewTutorState,
        get_route_param_or_error=Mock(side_effect=[4, 3, 2]),
        _user_may_view_submission=Mock(return_value=True),
    )
    on_load = inspect.unwrap(tutor_finished.BetaAIFinishedViewTutorState.on_load.fn)
    assert list(on_load(state)) == []
    evaluate.assert_called_once_with(session, result, result.finished_conversation)
    session.get.assert_not_called()
    assert state.exercise_title == "Test"
    assert state.current_lecture_id == 4


def test_combined_token_totals_keep_users_and_exercise_types():
    assert LectureTokenAnalyzerState._merge_user_token_totals(
        [("Alice", 10), ("Bob", None)], [("Alice", 20), ("Carol", 30)]
    ) == [("Alice", 30), ("Carol", 30), ("Bob", 0)]
    rows = LectureTokenAnalyzerState._rank_exercise_token_rows(
        [("Same title", 30), ("Unused", None)], [("Same title", 30)]
    )
    assert [(r.rank, r.exercise_title, r.tokens_used, r.is_beta) for r in rows] == [
        (1, "Same title", 30, False),
        (2, "Same title", 30, True),
        (3, "Unused", 0, False),
    ]


def test_trace_row_requires_analysis_consent_and_existing_exercise():
    session = Mock()
    state = Mock(
        spec=BetaAITraceLogsState,
        _trace_logs_for_result=Mock(return_value=[SimpleNamespace()]),
        _result_belongs_to_route=Mock(return_value=True),
    )
    for result in (
        None,
        SimpleNamespace(analysis_allowed=False),
        SimpleNamespace(analysis_allowed=True, beta_exercise=None),
    ):
        session.get.return_value = result
        assert BetaAITraceLogsState._trace_row_for_result(state, session, 1) is None


@pytest.mark.parametrize(
    "role,admin,lecture_id,expected",
    [
        (LectureRole.STUDENT, False, 4, False),
        (LectureRole.TUTOR, False, 4, True),
        (LectureRole.OWNER, False, 4, True),
        (None, False, 4, False),
        (LectureRole.TUTOR, False, None, False),
        (None, True, None, True),
        (None, True, 4, True),
    ],
)
def test_trace_permissions_use_real_membership_query(
    monkeypatch, role, admin, lecture_id, expected
):
    engine = create_engine("sqlite://")
    SQLModel.metadata.tables["linkuserlecture"].create(engine)
    try:
        with Session(engine) as session:
            if role is not None:
                session.add(LinkUserLecture(lecture_id=4, user_id=2, role=role))
                session.commit()

            @contextmanager
            def session_context():
                yield session

            monkeypatch.setattr(trace_state.rx, "session", session_context)
            state = Mock(
                spec=BetaAITraceLogsState,
                is_authenticated=True,
                authenticated_user=SimpleNamespace(id=2),
                global_permissions=[GlobalPermission.ADMIN] if admin else [],
                _route_lecture_id=Mock(return_value=lecture_id),
            )
            assert BetaAITraceLogsState._can_access_route(state) is expected
    finally:
        engine.dispose()
