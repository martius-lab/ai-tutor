"""Regression tests for Level AI chat persistence and submission."""

import asyncio
import inspect
from contextlib import contextmanager
from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock, Mock
from zoneinfo import ZoneInfo

import pytest
import reflex as rx

from aitutor.beta_ai.diagnosis import DiagnosisResponse
from aitutor.beta_ai.tutor_turn import TutorTurnResponse
from aitutor.global_vars import TIME_ZONE
from aitutor.models import BetaExercise
from aitutor.pages.beta_ai_chat import state as chat
from aitutor.pages.beta_ai_chat.components import beta_submit_button


@pytest.mark.parametrize("overdue", [True, False])
def test_submission_rechecks_deadline(monkeypatch, overdue):
    exercise = BetaExercise(
        title="Test",
        lecture_id=1,
        deadline=datetime.now(ZoneInfo(TIME_ZONE))
        + timedelta(days=-1 if overdue else 1),
    )
    result = SimpleNamespace(completed_at=None)
    session = Mock()
    session.get.return_value = exercise
    session.exec.return_value.one_or_none.return_value = result

    @contextmanager
    def session_context():
        yield session

    monkeypatch.setattr(chat.rx, "session", session_context)
    state = SimpleNamespace(
        running_diagnosis=False,
        _has_current_chat_access=lambda: True,
        completion_unlocked=True,
        current_beta_exercise_id=1,
        current_userinfo_id=2,
        messages=[{"role": "student", "content": "Answer"}],
        language="en",
        conversation_is_submitted=False,
    )
    submit = inspect.unwrap(chat.BetaAIChatState.submit_beta_conversation.fn)
    submit(state)
    assert state.is_overdue is overdue
    assert state.conversation_is_submitted is not overdue
    assert session.commit.call_count == (0 if overdue else 1)


def test_submission_does_not_run_during_diagnosis():
    state = SimpleNamespace(running_diagnosis=True)
    submit = inspect.unwrap(chat.BetaAIChatState.submit_beta_conversation.fn)
    assert submit(state) is None


def test_trace_keeps_answered_concept_after_transition(monkeypatch):
    session = Mock()
    session.exec.return_value.all.return_value = []

    @contextmanager
    def session_context():
        yield session

    monkeypatch.setattr(chat.rx, "session", session_context)
    state = SimpleNamespace(
        current_beta_exercise_id=1,
        current_userinfo_id=2,
        selected_concept_id=20,
    )
    cast(rx.EventHandler, chat.BetaAIChatState.append_trace_to_db).fn(
        state,
        beta_exercise_result_id=3,
        beta_concept_id=10,
        trace_entry={"concept_label": "Answered concept"},
    )
    trace = session.add.call_args.args[0]
    assert trace.beta_concept_id == 10
    assert trace.concept_label == "Answered concept"
    assert trace.turn_index == 1


def test_save_forwards_answered_concept_id():
    state = Mock(
        spec=chat.BetaAIChatState,
        save_conversation_to_db=Mock(return_value=3),
        append_trace_to_db=Mock(return_value=(4, 5)),
    )
    trace = {"concept_label": "Answered concept"}
    chat.BetaAIChatState._save_conversation_and_trace(state, trace, beta_concept_id=10)
    state.append_trace_to_db.assert_called_once_with(
        beta_exercise_result_id=3, beta_concept_id=10, trace_entry=trace
    )
    assert state.last_trace_log_id == 4
    assert state.trace_history_count == 5


def test_append_tutor_turn_updates_question_context():
    state = SimpleNamespace(messages=[], language="en")
    turn = TutorTurnResponse(
        feedback_brief="Good start.",
        next_question="Why?",
        question_level="explain_reasoning",
        focus_core_point_id=14,
    )
    cast(rx.EventHandler, chat.BetaAIChatState.append_tutor_turn_message).fn(
        state, turn
    )
    assert state.messages[0]["role"] == "tutor"
    assert "Good start." in state.messages[0]["content"]
    assert state.current_question == "Why?"
    assert state.current_question_level == "explain_reasoning"
    assert state.current_focus_core_point_id == 14


def test_submit_button_constructs_with_reflex_condition():
    assert beta_submit_button() is not None


def test_completion_trace_retains_finished_concept_context(monkeypatch):
    class ChatContext(SimpleNamespace):
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

    diagnosis = DiagnosisResponse(diagnosis_pattern="sufficient_for_completion")
    monkeypatch.setattr(
        chat, "run_structured_llm_diagnosis", AsyncMock(return_value=diagnosis)
    )
    monkeypatch.setattr(
        chat,
        "validate_and_normalize_diagnosis",
        Mock(
            return_value=SimpleNamespace(
                diagnosis=diagnosis,
                llm_suggested_pattern=diagnosis.diagnosis_pattern,
                errors=[],
                warnings=[],
            )
        ),
    )
    monkeypatch.setattr(chat, "preview_policy_action", Mock())
    monkeypatch.setattr(
        chat,
        "build_diagnosis_trace",
        Mock(return_value=SimpleNamespace(model_dump=dict)),
    )
    state = ChatContext(
        _has_current_chat_access=lambda: True,
        student_message="My answer",
        token_limit_reached=False,
        selected_concept_id=10,
        running_diagnosis=False,
        messages=[],
        exercise_title="Exercise",
        selected_concept_label="Finished concept",
        selected_concept_description="Description",
        core_points=[],
        misconceptions=[],
        current_question="Explain",
        current_question_level="apply_or_compare",
        current_focus_core_point_id=None,
        level_status={"apply_or_compare": "passed"},
        cumulative_covered_core_point_ids=[],
        cumulative_missing_core_point_ids=[],
        save_conversation_to_db=Mock(),
        build_cumulative_diagnosis=Mock(return_value=diagnosis),
        concept_state="secure",
        active_misconceptions=[{"label": "Old active"}],
        resolved_misconceptions=[{"label": "Old resolved"}],
        save_last_policy_action_to_student_state=Mock(),
        generate_concept_intro_turn=AsyncMock(return_value=TutorTurnResponse()),
        append_tutor_turn_message=Mock(),
        _save_conversation_and_trace=Mock(),
    )

    def advance():
        state.selected_concept_id = 20
        state.level_status = {}
        state.active_misconceptions = []
        state.resolved_misconceptions = []
        return {"advanced": True, "previous_label": "Finished concept"}

    state.advance_to_next_incomplete_concept = advance

    async def run_turn():
        async for _ in chat.BetaAIChatState.send_message.fn(state):
            pass

    asyncio.run(run_turn())
    trace = state._save_conversation_and_trace.call_args.args[0]
    assert state._save_conversation_and_trace.call_args.kwargs == {
        "beta_concept_id": 10
    }
    assert trace["active_misconceptions"] == [{"label": "Old active"}]
    assert trace["resolved_misconceptions"] == [{"label": "Old resolved"}]
    assert trace["level_status"] == {"apply_or_compare": "passed"}
    assert trace["next_concept_level_status"] == {}
    assert state.running_diagnosis is False
