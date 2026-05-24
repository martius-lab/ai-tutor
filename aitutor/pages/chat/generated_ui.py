"""Contracts and helpers for generated chat UI actions."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class GeneratedUiKind(StrEnum):
    """Supported generated UI action kinds."""

    SHOW_QUIZ = "show_quiz"


class QuizOption(BaseModel):
    """One selectable answer option in a generated quiz."""

    label: str = Field(min_length=1, max_length=240)


class QuizQuestion(BaseModel):
    """One multiple-choice question in a generated quiz."""

    question: str = Field(min_length=1, max_length=600)
    options: list[QuizOption] = Field(min_length=2, max_length=6)
    correct_option_index: int | None = Field(default=None, ge=0, le=5)
    explanation: str = Field(default="", max_length=1000)
    selected_option_index: int | None = Field(default=None, ge=0, le=5)

    @field_validator("correct_option_index", "selected_option_index")
    @classmethod
    def option_index_must_exist(cls, value: int | None, info):
        """Ensure option indexes point to existing options."""
        if value is None:
            return value

        options = info.data.get("options", [])
        if options and value >= len(options):
            raise ValueError("option index must point to an existing option")
        return value


class ShowQuizAction(BaseModel):
    """A generated multiple-choice quiz shown inline in the chat."""

    kind: Literal[GeneratedUiKind.SHOW_QUIZ] = GeneratedUiKind.SHOW_QUIZ
    title: str = Field(default="Quiz", max_length=120)
    questions: list[QuizQuestion] = Field(min_length=1, max_length=10)
    current_question_index: int = Field(default=0, ge=0, le=9)
    require_answer_before_continuing: bool = True

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_single_question(cls, data):
        """Accept persisted one-question quiz actions from older local runs."""
        if not isinstance(data, dict) or "questions" in data:
            return data

        if "question" not in data or "options" not in data:
            return data

        return {
            "kind": data.get("kind", GeneratedUiKind.SHOW_QUIZ),
            "title": data.get("title", "Quiz"),
            "current_question_index": data.get("current_question_index", 0),
            "questions": [
                {
                    "question": data.get("question"),
                    "options": data.get("options"),
                    "correct_option_index": data.get("correct_option_index"),
                    "explanation": data.get("explanation", ""),
                    "selected_option_index": data.get("selected_option_index"),
                }
            ],
            "require_answer_before_continuing": data.get(
                "require_answer_before_continuing", True
            ),
        }


class TutorResponse(BaseModel):
    """Structured response returned by the tutoring model."""

    message: str = Field(min_length=1)
    ui_actions: list[ShowQuizAction] = Field(default_factory=list, max_length=2)


GENERATIVE_UI_SYSTEM_PROMPT = """
You can use generated UI actions to make tutoring interactive.

Return every reply as structured data with:
- message: concise markdown text for the student.
- ui_actions: optional UI actions for the app to render.

Supported UI action:
- show_quiz: render a short multiple-choice quiz inline in the chat.

Use show_quiz when a short comprehension check, misconception check, or retrieval
practice question would help. A quiz may contain 1 to 10 questions. Keep most quizzes
small unless the student explicitly asks for a longer quiz. Do not use a quiz for
every reply. If the lesson context clearly determines an answer, include that
question's correct_option_index and a short explanation. If not, leave
correct_option_index null.
""".strip()


def sanitize_conversation_for_openai(conversation: list[dict]) -> list[dict[str, str]]:
    """Keep only OpenAI-supported chat message fields."""
    supported_roles = {"system", "user", "assistant"}
    return [
        {"role": str(msg["role"]), "content": str(msg["content"])}
        for msg in conversation
        if msg.get("role") in supported_roles and msg.get("content") is not None
    ]


def ui_actions_from_raw(raw_actions: object) -> list[ShowQuizAction]:
    """Parse persisted generated UI payloads and drop invalid stale actions."""
    if not isinstance(raw_actions, list):
        return []

    actions: list[ShowQuizAction] = []
    for raw_action in raw_actions:
        try:
            actions.append(ShowQuizAction.model_validate(raw_action))
        except ValueError:
            continue
    return actions


def quiz_result_message(action: ShowQuizAction) -> str:
    """Build the synthetic user turn that reports a completed quiz."""
    lines = [
        "Quiz result:",
        f"Quiz title: {action.title}",
    ]

    for index, question in enumerate(action.questions, start=1):
        selected_index = question.selected_option_index
        lines.append(f"\nQuestion {index}: {question.question}")
        if selected_index is None:
            lines.append("Selected answer: <not answered>")
            continue

        selected_answer = question.options[selected_index].label
        lines.append(f'Selected answer: "{selected_answer}"')

        if question.correct_option_index is not None:
            correct_answer = question.options[question.correct_option_index].label
            result = (
                "correct"
                if selected_index == question.correct_option_index
                else "wrong"
            )
            lines.extend(
                [
                    f"Result: {result}",
                    f'Correct answer: "{correct_answer}"',
                ]
            )

        if question.explanation:
            lines.append(f"Explanation shown to student: {question.explanation}")

    return "\n".join(lines)
