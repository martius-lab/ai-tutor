"""State for managing independent Beta AI Tutor exercises."""

import io

import pdfplumber
import reflex as rx
from sqlmodel import select

from aitutor.auth.protection import state_require_role_or_permission
from aitutor.auth.state import SessionState
from aitutor.beta_ai.concept_generation import generate_concepts_from_material
from aitutor.beta_ai.schemas import (
    EditableConcept,
    EditableCorePoint,
    EditableMisconception,
)
from aitutor.models import (
    BetaConcept,
    BetaCorePoint,
    BetaExercise,
    BetaMisconception,
    GlobalPermission,
)


class BetaAIExercisesState(SessionState):
    """State for the UI-first Beta AI exercise builder."""

    beta_exercises: list[BetaExercise] = []
    title: str = ""
    description: str = ""
    source_material_text: str = ""
    source_material_filename: str = ""
    generated_concepts: list[EditableConcept] = []
    extracting_source_material: bool = False
    generating_concepts: bool = False
    saving_exercise: bool = False

    @rx.event
    def set_title(self, value: str):
        """Set beta exercise title."""
        self.title = value

    @rx.event
    def set_description(self, value: str):
        """Set beta exercise description."""
        self.description = value

    @rx.event
    @state_require_role_or_permission(allowed_permissions=[GlobalPermission.LECTURER])
    def on_load(self):
        """Initialize the page."""
        self.global_load()
        self.load_beta_exercises()

    def on_logout(self):
        """Clear state on logout."""
        self.beta_exercises = []
        self.reset_builder()

    @rx.var
    def source_material_preview(self) -> str:
        """Short preview of the extracted source material."""
        if len(self.source_material_text) <= 800:
            return self.source_material_text
        return self.source_material_text[:800] + " ..."

    @rx.var
    def can_generate_concepts(self) -> bool:
        """Whether the concept-generation button should be enabled."""
        return bool(
            self.title.strip()
            and self.description.strip()
            and self.source_material_text.strip()
            and not self.generating_concepts
        )

    @rx.var
    def can_save_exercise(self) -> bool:
        """Whether the save button should be enabled."""
        return bool(
            self.title.strip()
            and self.description.strip()
            and self.source_material_text.strip()
            and self.generated_concepts
            and not self.saving_exercise
        )

    @rx.event
    def reset_builder(self):
        """Reset the current builder form."""
        self.title = ""
        self.description = ""
        self.source_material_text = ""
        self.source_material_filename = ""
        self.generated_concepts = []
        self.extracting_source_material = False
        self.generating_concepts = False
        self.saving_exercise = False

    @rx.event
    def load_beta_exercises(self):
        """Load saved Beta AI exercises."""
        with rx.session() as session:
            self.beta_exercises = list(
                session.exec(
                    select(BetaExercise).order_by(BetaExercise.id.desc())  # type: ignore
                ).all()
            )

    @rx.event
    async def extract_source_material(self, files: list[rx.UploadFile]):
        """Extract source material text from uploaded PDFs."""
        self.extracting_source_material = True
        yield

        try:
            text_parts: list[str] = []
            file_names: list[str] = []
            for file in files:
                upload_data = await file.read()
                with pdfplumber.open(io.BytesIO(upload_data)) as pdf:
                    text = "".join(page.extract_text() or "" for page in pdf.pages)
                text_parts.append(" ".join(text.replace("\n", " ").split()))
                file_names.append(file.name or "<unnamed file>")

            self.source_material_text = "\n\n".join(text_parts)
            self.source_material_filename = ", ".join(file_names)
        except Exception as exc:
            self.extracting_source_material = False
            yield rx.toast.error(f"Failed to extract PDF text: {exc}")
            return

        self.extracting_source_material = False
        yield rx.toast.success("PDF text extracted.")

    @rx.event(background=True)
    async def generate_concepts(self):
        """Generate editable concepts from the current source material."""
        async with self:
            if not self.can_generate_concepts:
                return
            self.generating_concepts = True
            title = self.title
            description = self.description
            source_material_text = self.source_material_text
        yield

        try:
            response = await generate_concepts_from_material(
                title=title,
                description=description,
                source_material_text=source_material_text,
            )
        except Exception as exc:
            async with self:
                self.generating_concepts = False
            yield rx.toast.error(f"Concept generation failed: {exc}")
            return

        async with self:
            self.generated_concepts = [
                EditableConcept(
                    concept_id=concept.concept_id,
                    label=concept.label,
                    description=concept.description,
                    core_points=[
                        EditableCorePoint(text=core_point)
                        for core_point in concept.core_points
                    ],
                    misconceptions=[
                        EditableMisconception(label=misconception)
                        for misconception in concept.misconceptions
                    ],
                )
                for concept in response.concepts
            ]
            self.generating_concepts = False
        yield rx.toast.success("Concepts generated. Please review them before saving.")

    @rx.event
    def set_concept_label(self, concept_index: int, value: str):
        """Set concept label."""
        self.generated_concepts[concept_index].label = value

    @rx.event
    def set_concept_description(self, concept_index: int, value: str):
        """Set concept description."""
        self.generated_concepts[concept_index].description = value

    @rx.event
    def set_core_point_text(
        self, concept_index: int, core_point_index: int, value: str
    ):
        """Set core point text."""
        self.generated_concepts[concept_index].core_points[
            core_point_index
        ].text = value

    @rx.event
    def set_core_point_required(
        self, concept_index: int, core_point_index: int, value: bool
    ):
        """Set whether a core point is required."""
        self.generated_concepts[concept_index].core_points[
            core_point_index
        ].required = value

    @rx.event
    def set_misconception_label(
        self, concept_index: int, misconception_index: int, value: str
    ):
        """Set misconception label."""
        self.generated_concepts[concept_index].misconceptions[
            misconception_index
        ].label = value

    @rx.event
    def add_concept(self):
        """Add an empty concept manually."""
        self.generated_concepts.append(
            EditableConcept(
                concept_id=f"manual.concept-{len(self.generated_concepts) + 1}",
                label="New concept",
                core_points=[EditableCorePoint()],
            )
        )

    @rx.event
    def delete_concept(self, concept_index: int):
        """Delete a concept."""
        del self.generated_concepts[concept_index]

    @rx.event
    def add_core_point(self, concept_index: int):
        """Add a core point."""
        self.generated_concepts[concept_index].core_points.append(EditableCorePoint())

    @rx.event
    def delete_core_point(self, concept_index: int, core_point_index: int):
        """Delete a core point."""
        del self.generated_concepts[concept_index].core_points[core_point_index]

    @rx.event
    def add_misconception(self, concept_index: int):
        """Add a misconception."""
        self.generated_concepts[concept_index].misconceptions.append(
            EditableMisconception()
        )

    @rx.event
    def delete_misconception(self, concept_index: int, misconception_index: int):
        """Delete a misconception."""
        del self.generated_concepts[concept_index].misconceptions[misconception_index]

    @rx.event
    def save_beta_exercise(self):
        """Persist the exercise and reviewed concepts."""
        if not self.can_save_exercise:
            return rx.toast.error("Please generate or add at least one concept first.")

        self.saving_exercise = True
        with rx.session() as session:
            exercise = BetaExercise(
                title=self.title,
                description=self.description,
                source_material_text=self.source_material_text,
                source_material_filename=self.source_material_filename,
            )
            session.add(exercise)
            session.flush()
            if exercise.id is None:
                raise ValueError("Failed to create beta exercise id.")

            for concept_index, concept in enumerate(self.generated_concepts):
                db_concept = BetaConcept(
                    beta_exercise_id=exercise.id,
                    concept_id=concept.concept_id,
                    label=concept.label,
                    description=concept.description,
                    order_index=concept_index,
                )
                session.add(db_concept)
                session.flush()
                if db_concept.id is None:
                    raise ValueError("Failed to create beta concept id.")

                for core_point_index, core_point in enumerate(concept.core_points):
                    if core_point.text.strip():
                        session.add(
                            BetaCorePoint(
                                beta_concept_id=db_concept.id,
                                text=core_point.text,
                                required=core_point.required,
                                order_index=core_point_index,
                            )
                        )

                for misconception_index, misconception in enumerate(
                    concept.misconceptions
                ):
                    if misconception.label.strip():
                        session.add(
                            BetaMisconception(
                                beta_concept_id=db_concept.id,
                                label=misconception.label,
                                order_index=misconception_index,
                            )
                        )

            session.commit()

        self.saving_exercise = False
        self.reset_builder()
        self.load_beta_exercises()
        return rx.toast.success("Beta AI exercise saved.")
