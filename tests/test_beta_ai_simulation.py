"""Regression tests for the terminal Level AI simulator."""

import asyncio
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock

import pytest
from sqlmodel import Session, SQLModel, create_engine

from aitutor.beta_ai.diagnosis import DiagnosisResponse
from aitutor.beta_ai.tutor_turn import TutorTurnResponse
from aitutor.models import (
    BetaConcept,
    BetaCorePoint,
    BetaExercise,
    BetaStudentConceptState,
)
from scripts import simulate_beta_ai_exercise as sim


def bundle(concept_id=10):
    return sim.ConceptBundle(
        concept=BetaConcept(id=concept_id, beta_exercise_id=1, label="ReLU"),
        core_points=[
            BetaCorePoint(id=20, beta_concept_id=concept_id, text="Nonlinearity")
        ],
        misconceptions=[],
        student_state=BetaStudentConceptState(
            userinfo_id=0, beta_exercise_id=1, beta_concept_id=concept_id
        ),
    )


@pytest.mark.parametrize(
    "option", ["--max-concepts", "--max-total-turns", "--max-turns-per-concept"]
)
def test_cli_rejects_zero_limits(option):
    with pytest.raises(SystemExit):
        sim.parse_args(["--exercise-id", "1", option, "0"])


def test_cli_rejects_unknown_batch_persona():
    with pytest.raises(SystemExit):
        sim.parse_args(["--exercise-id", "1", "--personas", "strong,typo"])


def test_fuzzy_title_requires_unambiguous_match():
    session = SimpleNamespace(
        exec=lambda _: SimpleNamespace(
            all=lambda: [
                BetaExercise(id=1, title="Lecture A"),
                BetaExercise(id=2, title="Lecture B"),
            ]
        )
    )
    with pytest.raises(ValueError, match="Ambiguous"):
        sim.find_exercise(cast(Session, session), "Lecture")
    assert sim.find_exercise(cast(Session, session), "Lecture A").id == 1


def test_three_levels_and_higher_level_repair(monkeypatch):
    data = bundle()
    answer = "Meine eigene Erklärung enthält eine fachliche Beziehung und ein Beispiel."
    monkeypatch.setattr(
        sim, "generate_mediocre_student_answer", AsyncMock(return_value=answer)
    )
    diagnoses = [
        DiagnosisResponse(
            task_relevance=1,
            correctness=1,
            completeness=1,
            covered_core_point_ids=[20],
            evidence_snippets=[answer],
            diagnosis_pattern="sufficient_for_completion",
        ),
        DiagnosisResponse(
            task_relevance=1,
            correctness=0.4,
            completeness=0.3,
            evidence_snippets=[answer],
            diagnosis_pattern="correct_but_incomplete",
        ),
    ]
    monkeypatch.setattr(
        sim,
        "run_llm_diagnosis",
        AsyncMock(side_effect=[diagnoses[0], diagnoses[1], diagnoses[0], diagnoses[0]]),
    )
    transition = AsyncMock(
        side_effect=[
            TutorTurnResponse(
                next_question="Welche Konsequenz folgt?",
                question_level="explain_reasoning",
            ),
            TutorTurnResponse(
                next_question="Vergleiche zwei Fälle.",
                question_level="apply_or_compare",
            ),
        ]
    )
    monkeypatch.setattr(sim, "run_level_transition_question_generation", transition)
    repair = AsyncMock(
        return_value=TutorTurnResponse(
            next_question="Begründe diese Beziehung genauer.",
            question_level="explain_reasoning",
        )
    )
    monkeypatch.setattr(sim, "run_tutor_turn_generation", repair)
    state = sim.SimulationState(current_question="Erkläre die Grundidee.")
    exercise = BetaExercise(id=1, title="Activation functions")
    entries = []
    for turn in range(1, 5):
        entries.append(
            asyncio.run(
                sim.simulate_turn(
                    exercise=exercise,
                    bundle=data,
                    sim_state=state,
                    turn_in_concept=turn,
                    persona="strong",
                )
            )
        )
    assert entries[0]["policy"]["rule_id"] == "R-ASK-HOLISTIC-EXPLAIN-01"
    assert entries[1]["policy"]["rule_id"] == "R-EXPLAIN-CLARIFY-01"
    assert entries[2]["policy"]["rule_id"] == "R-ASK-APPLY-01"
    assert data.student_state.state == "secure"
    assert entries[3]["tutor_turn"]["next_question"] == ""
    assert [e["current_question_level"] for e in entries] == [
        "basic_understanding",
        "explain_reasoning",
        "explain_reasoning",
        "apply_or_compare",
    ]
    assert transition.await_count == 2
    assert repair.await_count == 1
    assert transition.await_args_list[0].kwargs["student_answer"] == answer
    report = sim.render_markdown(
        exercise=exercise,
        bundles=[data],
        trace=entries,
        completed_all=True,
        persona="strong",
        stop_reason="completed_selected_concepts",
    )
    assert "`basic_understanding` → `explain_reasoning`" in report
    assert "Answered question: Erkläre die Grundidee." in report
    assert "Concept complete; no follow-up question" in report
    assert "Policy-facing pattern" in report
    assert "Current-answer covered IDs" in report
    assert "Accumulated covered IDs" in report
    assert "Newly passed levels this turn" in report


def test_turn_limit_does_not_skip_incomplete_concept(monkeypatch, tmp_path):
    db = tmp_path / "simulation.db"
    engine = create_engine(f"sqlite:///{db}")
    SQLModel.metadata.tables["betaexercise"].create(engine)
    with Session(engine) as session:
        session.add(BetaExercise(id=1, title="Example"))
        session.commit()
    bundles = [bundle(10), bundle(11)]
    monkeypatch.setattr(sim, "load_concept_bundles", lambda *_: bundles)
    monkeypatch.setattr(
        sim, "get_config", lambda: SimpleNamespace(level_ai_model="test")
    )
    monkeypatch.setattr(sim, "get_env_settings", lambda: None)
    turn = AsyncMock(
        return_value={
            "current_question_level": "basic_understanding",
            "cumulative_diagnosis": {"diagnosis_pattern": "off_task"},
            "policy": {"rule_id": "R-OFFTASK-01"},
        }
    )
    monkeypatch.setattr(sim, "simulate_turn", turn)
    outputs = []
    monkeypatch.setattr(sim, "write_outputs", lambda **kwargs: outputs.append(kwargs))
    args = sim.parse_args(["--exercise-id", "1", "--max-turns-per-concept", "1"])
    args.db_url = f"sqlite:///{db}"
    asyncio.run(sim.run_simulation(args))
    assert turn.await_count == 1
    assert outputs[-1]["stop_reason"] == "max_turns_per_concept"
    assert not outputs[-1]["completed_all"]
    assert bundles[1].student_state.state == "unseen"


@pytest.mark.parametrize("persona", ["persistent_hint", "keyword_only", "copy_tutor"])
def test_negative_controls_never_pass_basic(monkeypatch, persona):
    data = bundle()
    question = "Was bedeutet Nichtlinearität?"
    monkeypatch.setattr(
        sim,
        "run_llm_diagnosis",
        AsyncMock(
            return_value=DiagnosisResponse(
                task_relevance=1,
                correctness=1,
                completeness=1,
                covered_core_point_ids=[20],
                diagnosis_pattern="sufficient_for_completion",
                student_intent=(
                    "hint_request" if persona == "persistent_hint" else "answer_attempt"
                ),
                is_answer_attempt=persona != "persistent_hint",
            )
        ),
    )
    monkeypatch.setattr(
        sim,
        "run_tutor_turn_generation",
        AsyncMock(
            return_value=TutorTurnResponse(
                next_question=question,
                question_level="basic_understanding",
            )
        ),
    )
    state = sim.SimulationState(
        current_question=question,
        messages=[{"role": "tutor", "content": question}],
    )
    for turn in range(1, 4):
        entry = asyncio.run(
            sim.simulate_turn(
                exercise=BetaExercise(id=1, title="Example"),
                bundle=data,
                sim_state=state,
                turn_in_concept=turn,
                persona=persona,
            )
        )
        assert data.student_state.state != "secure"
        assert entry["student_state"]["covered_core_point_ids"] == []
        assert "passed" not in entry["student_state"]["level_status"].values()


def test_dialogue_context_hides_rubric(monkeypatch):
    create = AsyncMock(
        return_value=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="Eine Antwort"))],
        )
    )
    monkeypatch.setattr(
        sim,
        "AsyncOpenAI",
        lambda **_: SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create)),
        ),
    )
    monkeypatch.setattr(
        sim,
        "get_env_settings",
        lambda: SimpleNamespace(
            OPENAI_API_KEY="test",
            OPENAI_BASE_URL=None,
        ),
    )
    monkeypatch.setattr(
        sim, "get_config", lambda: SimpleNamespace(level_ai_model="test")
    )
    data = bundle()
    asyncio.run(
        sim.generate_mediocre_student_answer(
            concept=data.concept,
            core_points=data.core_points,
            misconceptions=[],
            student_state=data.student_state,
            question="Was bedeutet das?",
            question_level="basic_understanding",
            turn_in_concept=1,
            messages=[],
            persona="strong",
            student_context="dialogue",
        )
    )
    assert create.await_args is not None
    prompt = create.await_args.kwargs["messages"][1]["content"]
    assert "Nonlinearity" not in prompt
    assert "Still missing ideas" not in prompt
    assert "No hidden rubric" in prompt
