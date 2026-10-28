from types import SimpleNamespace

from aitutor.global_vars import LEVEL_AI_MAX_SOURCE_MATERIAL_CHARS
from aitutor.pages.lecture_manage_exercises.level_ai_builder_state import (
    BetaAIExercisesState,
)


def _exceeds_limit(text: str) -> bool:
    state = SimpleNamespace(source_material_text=text)
    return BetaAIExercisesState.source_material_exceeds_limit.fget(state)  # type: ignore[attr-defined]


def test_material_up_to_the_limit_is_used_completely():
    assert not _exceeds_limit("x" * LEVEL_AI_MAX_SOURCE_MATERIAL_CHARS)


def test_longer_material_is_flagged_as_truncated():
    assert _exceeds_limit("x" * (LEVEL_AI_MAX_SOURCE_MATERIAL_CHARS + 1))
