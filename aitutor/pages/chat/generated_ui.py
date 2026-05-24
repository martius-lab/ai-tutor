"""Contracts and helpers for generated chat UI actions."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class GeneratedUiKind(StrEnum):
    """Supported generated UI action kinds."""

    SHOW_QUIZ = "show_quiz"
    SHOW_DIAGRAM = "show_diagram"


class DiagramType(StrEnum):
    """Supported generated diagram layouts."""

    FLOW = "flow"
    CYCLE = "cycle"
    COMPARISON = "comparison"
    TREE = "tree"
    NETWORK = "network"


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


class DiagramNode(BaseModel):
    """One node in a generated diagram."""

    id: str = Field(min_length=1, max_length=40)
    label: str = Field(min_length=1, max_length=80)
    detail: str = Field(default="", max_length=240)


class DiagramEdge(BaseModel):
    """One relationship between two generated diagram nodes."""

    source_id: str = Field(min_length=1, max_length=40)
    target_id: str = Field(min_length=1, max_length=40)
    label: str = Field(default="", max_length=120)


class GeneratedUiAction(BaseModel):
    """A generated UI action shown inline in the chat."""

    kind: Literal[
        GeneratedUiKind.SHOW_QUIZ, GeneratedUiKind.SHOW_DIAGRAM
    ] = GeneratedUiKind.SHOW_QUIZ
    title: str = Field(default="Quiz", max_length=120)
    questions: list[QuizQuestion] = Field(default_factory=list, max_length=10)
    current_question_index: int = Field(default=0, ge=0, le=9)
    require_answer_before_continuing: bool = True
    diagram_type: DiagramType = DiagramType.FLOW
    nodes: list[DiagramNode] = Field(default_factory=list, max_length=12)
    edges: list[DiagramEdge] = Field(default_factory=list, max_length=16)
    caption: str = Field(default="", max_length=400)

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

    @model_validator(mode="after")
    def validate_action_payload(self):
        """Validate the payload required by each action kind."""
        if self.kind == GeneratedUiKind.SHOW_QUIZ:
            if not self.questions:
                raise ValueError("show_quiz requires at least one question")
            if self.current_question_index >= len(self.questions):
                raise ValueError("current_question_index must point to a question")
            return self

        if len(self.nodes) < 2:
            raise ValueError("show_diagram requires at least two nodes")

        node_ids = {node.id for node in self.nodes}
        if len(node_ids) != len(self.nodes):
            raise ValueError("diagram node ids must be unique")

        if len(self.edges) < len(self.nodes) - 1:
            raise ValueError("show_diagram requires edges between adjacent nodes")

        for edge in self.edges:
            if edge.source_id not in node_ids or edge.target_id not in node_ids:
                raise ValueError("diagram edges must reference existing node ids")

        return self


ShowQuizAction = GeneratedUiAction
ShowDiagramAction = GeneratedUiAction


class TutorResponse(BaseModel):
    """Structured response returned by the tutoring model."""

    message: str = Field(min_length=1)
    ui_actions: list[GeneratedUiAction] = Field(default_factory=list, max_length=2)


GENERATIVE_UI_SYSTEM_PROMPT = """
You can use generated UI actions to make tutoring interactive.

Return every reply as structured data with:
- message: concise markdown text for the student.
- ui_actions: optional UI actions for the app to render.

Supported UI action:
- show_quiz: render a short multiple-choice quiz inline in the chat.
- show_diagram: render a compact typed diagram inline in the chat.

Use show_quiz when a short comprehension check, misconception check, or retrieval
practice question would help. A quiz may contain 1 to 10 questions. Keep most quizzes
small unless the student explicitly asks for a longer quiz. Do not use a quiz for
every reply. If the lesson context clearly determines an answer, include that
question's correct_option_index and a short explanation. If not, leave
correct_option_index null.

The message field supports GitHub-flavored Markdown, including tables, links, bold
text, lists, inline code, and fenced code blocks.

Use show_diagram when a visual structure would help explain a process, system,
concept map, cycle, or comparison. Prefer diagram_type "tree" or "network" for
infographic-like concept maps; use "flow" only for strictly ordered steps, "cycle"
for repeating processes, and "comparison" for side-by-side concepts. Provide 2 to
12 nodes and at least one edge between each adjacent node in display order. Put the
central concept first when using "tree" or "network". Only use edges that reference
existing node ids. Do not generate HTML, SVG, Mermaid, or image prompts; use only
the typed nodes and edges.

Good show_diagram patterns:
- flow: ordered pipeline, timeline, algorithm, cause-and-effect chain. Nodes should
  be steps in order; edges should describe the transition between neighboring steps.
- tree/network: concept map, system overview, factors around one main concept. Put
  the central concept in nodes[0]; every other node should connect back to it with
  an edge label such as "uses", "produces", or "depends on".
- comparison: two or more concepts with short contrasting nodes and labeled edges.

Avoid:
- using flow for a general concept map.
- numbering concept-map nodes in the message text.
- dumping a long list when a Markdown table is clearer.
- repeating the same explanation in message and node details.
""".strip()


def sanitize_conversation_for_openai(conversation: list[dict]) -> list[dict[str, str]]:
    """Keep only OpenAI-supported chat message fields."""
    supported_roles = {"system", "user", "assistant"}
    return [
        {"role": str(msg["role"]), "content": str(msg["content"])}
        for msg in conversation
        if msg.get("role") in supported_roles and msg.get("content") is not None
    ]


def ui_actions_from_raw(raw_actions: object) -> list[GeneratedUiAction]:
    """Parse persisted generated UI payloads and drop invalid stale actions."""
    if not isinstance(raw_actions, list):
        return []

    actions: list[GeneratedUiAction] = []
    for raw_action in raw_actions:
        try:
            actions.append(GeneratedUiAction.model_validate(raw_action))
        except ValueError:
            continue
    return actions


def quiz_result_message(action: GeneratedUiAction) -> str:
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
