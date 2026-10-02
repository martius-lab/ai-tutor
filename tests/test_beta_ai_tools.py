"""Deterministic smoke tests for Level AI developer tools."""

import json

from aitutor.beta_ai.tutor_turn import TutorTurnResponse
from aitutor.pages.beta_ai_diagnosis_lab.components import (
    beta_ai_diagnosis_lab_content,
)
from scripts.evaluate_beta_ai_thresholds import analyze_simulation, render_report
from scripts.simulate_beta_ai_exercise import SimulationState, format_tutor_message


def test_simulation_defaults_and_tutor_format_are_unchanged():
    state = SimulationState()
    assert state.current_question_level == "basic_understanding"
    assert state.intro_transition_kind == "initial"
    turn = TutorTurnResponse(feedback_brief="Gut.", next_question="Warum?")
    assert format_tutor_message(turn) == "Gut.\n\nFrage: Warum?"


def test_evaluation_keeps_final_state_per_concept(tmp_path):
    path = tmp_path / "simulation.json"
    path.write_text(
        json.dumps(
            {
                "persona": "strong",
                "completed_all": True,
                "trace": [
                    {
                        "concept_id": 1,
                        "student_state": {"state": "in_progress"},
                    },
                    {"concept_id": 1, "student_state": {"state": "secure"}},
                    {"concept_id": 2, "student_state": {"state": "secure"}},
                ],
            }
        ),
        encoding="utf-8",
    )
    metrics = analyze_simulation(path)
    assert metrics.turn_count == 3
    assert metrics.completed_concepts == 2
    assert dict(metrics.final_states) == {"secure": 2}
    assert metrics.completed_all is True
    assert "strong" in render_report([metrics], tmp_path / "summary.json")


def test_diagnosis_lab_components_construct():
    assert beta_ai_diagnosis_lab_content() is not None
