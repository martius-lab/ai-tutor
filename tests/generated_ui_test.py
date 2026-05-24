"""Tests for generated chat UI contracts."""

import pytest

from aitutor.pages.chat.generated_ui import (
    DiagramType,
    GeneratedUiAction,
    GeneratedUiKind,
    ShowQuizAction,
    TutorResponse,
    quiz_result_message,
    sanitize_conversation_for_openai,
    ui_actions_from_raw,
)


def test_tutor_response_parses_show_quiz_action():
    """A structured tutor response can include a renderable quiz action."""
    response = TutorResponse.model_validate(
        {
            "message": "Check your understanding.",
            "ui_actions": [
                {
                    "kind": "show_quiz",
                    "title": "Arithmetic check",
                    "questions": [
                        {
                            "question": "Which value equals 2 + 2?",
                            "options": [{"label": "3"}, {"label": "4"}],
                            "correct_option_index": 1,
                            "explanation": "2 + 2 combines two pairs.",
                        }
                    ],
                }
            ],
        }
    )

    quiz = response.ui_actions[0]
    assert quiz.kind == GeneratedUiKind.SHOW_QUIZ
    assert quiz.questions[0].options[1].label == "4"
    assert quiz.questions[0].correct_option_index == 1


def test_tutor_response_parses_multiple_question_quiz():
    """A quiz action can contain up to 10 questions."""
    response = TutorResponse.model_validate(
        {
            "message": "Try a short quiz.",
            "ui_actions": [
                {
                    "kind": "show_quiz",
                    "title": "Two-question check",
                    "questions": [
                        {
                            "question": "Which gas do plants take in?",
                            "options": [{"label": "CO2"}, {"label": "O2"}],
                            "correct_option_index": 0,
                        },
                        {
                            "question": "Which sugar stores energy?",
                            "options": [{"label": "Glucose"}, {"label": "Water"}],
                            "correct_option_index": 0,
                        },
                    ],
                }
            ],
        }
    )

    assert len(response.ui_actions[0].questions) == 2


def test_quiz_option_indexes_must_exist():
    """Quiz indexes must point to one of the available options."""
    with pytest.raises(ValueError):
        ShowQuizAction.model_validate(
            {
                "questions": [
                    {
                        "question": "Pick one.",
                        "options": [{"label": "A"}, {"label": "B"}],
                        "correct_option_index": 2,
                    }
                ],
            }
        )


def test_tutor_response_parses_show_diagram_action():
    """A structured tutor response can include a renderable diagram action."""
    response = TutorResponse.model_validate(
        {
            "message": "Here is the process visually.",
            "ui_actions": [
                {
                    "kind": "show_diagram",
                    "title": "Photosynthesis map",
                    "diagram_type": "tree",
                    "nodes": [
                        {
                            "id": "light",
                            "label": "Photosynthesis",
                            "detail": "Chlorophyll captures energy.",
                        },
                        {
                            "id": "water",
                            "label": "Water split",
                            "detail": "Oxygen is released.",
                        },
                    ],
                    "edges": [
                        {
                            "source_id": "light",
                            "target_id": "water",
                            "label": "powers",
                        }
                    ],
                    "caption": "A compact process diagram.",
                }
            ],
        }
    )

    diagram = response.ui_actions[0]
    assert diagram.kind == GeneratedUiKind.SHOW_DIAGRAM
    assert diagram.diagram_type == DiagramType.TREE
    assert diagram.nodes[0].label == "Photosynthesis"


def test_diagram_edges_must_reference_existing_nodes():
    """Generated diagram edges must reference declared node ids."""
    with pytest.raises(ValueError):
        GeneratedUiAction.model_validate(
            {
                "kind": "show_diagram",
                "title": "Invalid diagram",
                "nodes": [
                    {"id": "a", "label": "A"},
                    {"id": "b", "label": "B"},
                ],
                "edges": [
                    {"source_id": "a", "target_id": "missing"},
                ],
            }
        )


def test_diagram_requires_edges_between_adjacent_nodes():
    """Generated diagram renderers expect an ordered edge between each node."""
    with pytest.raises(ValueError):
        GeneratedUiAction.model_validate(
            {
                "kind": "show_diagram",
                "title": "Under-connected diagram",
                "nodes": [
                    {"id": "a", "label": "A"},
                    {"id": "b", "label": "B"},
                    {"id": "c", "label": "C"},
                ],
                "edges": [
                    {"source_id": "a", "target_id": "b"},
                ],
            }
        )


def test_sanitize_conversation_removes_app_only_fields():
    """Only OpenAI-supported message fields are sent to the model."""
    sanitized = sanitize_conversation_for_openai(
        [
            {"role": "system", "content": "Tutor prompt", "check_passed": False},
            {
                "role": "assistant",
                "content": "Try this.",
                "ui_actions": [{"kind": "show_quiz"}],
            },
            {"role": "check_result", "content": "Private check"},
        ]
    )

    assert sanitized == [
        {"role": "system", "content": "Tutor prompt"},
        {"role": "assistant", "content": "Try this."},
    ]


def test_ui_actions_from_raw_drops_invalid_actions():
    """Invalid persisted actions should not break conversation loading."""
    actions = ui_actions_from_raw(
        [
            {
                "kind": "show_quiz",
                "questions": [
                    {
                        "question": "Pick one.",
                        "options": [{"label": "A"}, {"label": "B"}],
                    }
                ],
            },
            {"kind": "show_quiz", "questions": []},
        ]
    )

    assert len(actions) == 1
    assert actions[0].questions[0].question == "Pick one."


def test_ui_actions_from_raw_accepts_legacy_single_question_action():
    """Persisted one-question actions from older local runs still load."""
    actions = ui_actions_from_raw(
        [
            {
                "kind": "show_quiz",
                "question": "Pick one.",
                "options": [{"label": "A"}, {"label": "B"}],
                "selected_option_index": 1,
            }
        ]
    )

    assert actions[0].questions[0].selected_option_index == 1


def test_quiz_result_message_includes_selected_and_correct_answers():
    """The synthetic user turn gives the model enough context to continue."""
    action = ShowQuizAction.model_validate(
        {
            "title": "Arithmetic check",
            "questions": [
                {
                    "question": "Which value equals 2 + 2?",
                    "options": [{"label": "3"}, {"label": "4"}],
                    "correct_option_index": 1,
                    "selected_option_index": 0,
                    "explanation": "2 + 2 combines two pairs.",
                }
            ],
        }
    )

    result = quiz_result_message(action)

    assert 'Selected answer: "3"' in result
    assert 'Correct answer: "4"' in result
    assert "Result: wrong" in result
