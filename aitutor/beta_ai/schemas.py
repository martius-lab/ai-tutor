"""Shared Beta AI Tutor schemas used by UI state and domain helpers."""

from pydantic import BaseModel, Field


class EditableCorePoint(BaseModel):
    """Editable UI representation of a concept core point."""

    text: str = ""
    required: bool = True


class EditableMisconception(BaseModel):
    """Editable UI representation of a misconception hint."""

    label: str = ""


class EditableConcept(BaseModel):
    """Editable UI representation of a generated or manually added concept."""

    concept_id: str = ""
    label: str = ""
    description: str = ""
    core_points: list[EditableCorePoint] = Field(default_factory=list)
    misconceptions: list[EditableMisconception] = Field(default_factory=list)


class SavedConceptDetail(BaseModel):
    """Read-only UI representation of a persisted Beta AI concept."""

    id: int
    concept_id: str = ""
    label: str = ""
    description: str = ""
    core_points: list[str] = Field(default_factory=list)
    misconceptions: list[str] = Field(default_factory=list)
