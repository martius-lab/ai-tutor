"""State for managing independent Beta AI Tutor exercises."""

import io

import pdfplumber
import reflex as rx
from sqlmodel import select

from aitutor.auth.protection import state_require_role_at_least
from aitutor.auth.state import SessionState
from aitutor.beta_ai.concept_generation import generate_concepts_from_material
from aitutor.beta_ai.schemas import (
    EditableConcept,
    EditableCorePoint,
    EditableMisconception,
    SavedConceptDetail,
)
from aitutor.models import (
    BetaConcept,
    BetaCorePoint,
    BetaExercise,
    BetaMisconception,
    UserRole,
)


class BetaAIExercisesState(SessionState):
    """State for the UI-first Beta AI exercise builder."""

    MIN_GENERATION_TARGET: int = 1
    MAX_CONCEPT_TARGET: int = 30
    MAX_CORE_POINT_TARGET: int = 15
    MAX_MISCONCEPTION_TARGET: int = 10

    beta_exercises: list[BetaExercise] = []
    title: str = ""
    description: str = ""
    concept_target_count: int = 8
    core_point_target_count: int = 4
    misconception_target_count: int = 2
    source_material_text: str = ""
    source_material_filename: str = ""
    generated_concepts: list[EditableConcept] = []
    selected_saved_exercise_id: int | None = None
    selected_saved_exercise_title: str = ""
    selected_saved_exercise_description: str = ""
    selected_saved_exercise_source_file: str = ""
    selected_saved_concepts: list[SavedConceptDetail] = []
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
    def set_concept_target_count(self, value: str):
        """Set the approximate number of concepts to generate."""
        self._set_generation_target(
            "concept_target_count", value, self.MAX_CONCEPT_TARGET
        )

    @rx.event
    def set_core_point_target_count(self, value: str):
        """Set the approximate number of core points per concept."""
        self._set_generation_target(
            "core_point_target_count", value, self.MAX_CORE_POINT_TARGET
        )

    @rx.event
    def set_misconception_target_count(self, value: str):
        """Set the approximate number of misconceptions per concept."""
        self._set_generation_target(
            "misconception_target_count", value, self.MAX_MISCONCEPTION_TARGET
        )

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
    def set_misconception_label(
        self, concept_index: int, misconception_index: int, value: str
    ):
        """Set misconception label."""
        self.generated_concepts[concept_index].misconceptions[
            misconception_index
        ].label = value

    @rx.event
    @state_require_role_at_least(UserRole.TUTOR)
    def on_load(self):
        """Initialize the page."""
        self.global_load()
        self.load_beta_exercises()

    def on_logout(self):
        """Clear state on logout."""
        self.beta_exercises = []
        self.reset_builder()
        self.clear_selected_saved_exercise()

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
            and self.source_material_text.strip()
            and not self.generating_concepts
        )

    @rx.var
    def can_save_exercise(self) -> bool:
        """Whether the save button should be enabled."""
        return bool(
            self.title.strip()
            and self.source_material_text.strip()
            and self.generated_concepts
            and not self.saving_exercise
        )

    @rx.var
    def generate_concepts_button_label(self) -> str:
        """Return a clear generate/regenerate button label."""
        if self.generated_concepts:
            return "Regenerate Concepts (replaces current list)"
        return "Generate Concepts"

    @rx.var
    def concept_target_count_str(self) -> str:
        """Return the concept target count as a string for the input field."""
        return str(self.concept_target_count)

    @rx.var
    def core_point_target_count_str(self) -> str:
        """Return the core point target count as a string for the input field."""
        return str(self.core_point_target_count)

    @rx.var
    def misconception_target_count_str(self) -> str:
        """Return the misconception target count as a string for the input field."""
        return str(self.misconception_target_count)

    @rx.var
    def has_selected_saved_exercise(self) -> bool:
        """Whether a saved exercise is selected for inspection."""
        return self.selected_saved_exercise_id is not None

    def _set_generation_target(self, field_name: str, value: str, maximum: int):
        """Set a positive concept-generation target from a number input."""
        try:
            target = int(value)
        except ValueError:
            return
        setattr(self, field_name, max(self.MIN_GENERATION_TARGET, min(maximum, target)))

    def _validate_generated_concepts(self) -> str | None:
        """Return a user-facing validation error for the editable concept list."""
        if not self.generated_concepts:
            return "Please generate or add at least one concept first."

        for concept_index, concept in enumerate(self.generated_concepts, start=1):
            if not concept.label.strip():
                return f"Concept {concept_index} needs a non-empty label."

            has_core_point = any(
                core_point.text.strip() for core_point in concept.core_points
            )
            if not has_core_point:
                return (
                    f"Concept {concept_index} needs at least one non-empty core point."
                )

            for misconception_index, misconception in enumerate(
                concept.misconceptions, start=1
            ):
                if not misconception.label.strip():
                    return (
                        f"Concept {concept_index}, misconception "
                        f"{misconception_index} needs a non-empty label."
                    )

        return None

    def _beta_exercise_title_exists(self, title: str) -> bool:
        """Return whether a Beta AI exercise with this exact title already exists."""
        with rx.session() as session:
            existing_exercise = session.exec(
                select(BetaExercise).where(BetaExercise.title == title)
            ).first()
        return existing_exercise is not None

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
    def clear_selected_saved_exercise(self):
        """Clear the saved exercise detail inspector."""
        self.selected_saved_exercise_id = None
        self.selected_saved_exercise_title = ""
        self.selected_saved_exercise_description = ""
        self.selected_saved_exercise_source_file = ""
        self.selected_saved_concepts = []

    @rx.event
    def select_saved_exercise(self, exercise_id: int | None):
        """Load a saved Beta AI exercise and its concept registry for inspection."""
        if exercise_id is None:
            return

        with rx.session() as session:
            exercise = session.get(BetaExercise, exercise_id)
            if exercise is None:
                return rx.toast.error(
                    description="Beta AI exercise not found.",
                    duration=5000,
                    position="bottom-center",
                    invert=True,
                )

            concepts = list(
                session.exec(
                    select(BetaConcept)
                    .where(BetaConcept.beta_exercise_id == exercise_id)
                    .order_by(BetaConcept.order_index)  # type: ignore
                ).all()
            )
            concept_details = []
            for concept in concepts:
                if concept.id is None:
                    continue
                core_points = list(
                    session.exec(
                        select(BetaCorePoint)
                        .where(BetaCorePoint.beta_concept_id == concept.id)
                        .order_by(BetaCorePoint.order_index)  # type: ignore
                    ).all()
                )
                misconceptions = list(
                    session.exec(
                        select(BetaMisconception)
                        .where(BetaMisconception.beta_concept_id == concept.id)
                        .order_by(BetaMisconception.order_index)  # type: ignore
                    ).all()
                )
                concept_details.append(
                    SavedConceptDetail(
                        id=concept.id,
                        concept_id=concept.concept_id,
                        label=concept.label,
                        description=concept.description,
                        core_points=[core_point.text for core_point in core_points],
                        misconceptions=[
                            misconception.label for misconception in misconceptions
                        ],
                    )
                )

        self.selected_saved_exercise_id = exercise_id
        self.selected_saved_exercise_title = exercise.title
        self.selected_saved_exercise_description = exercise.description
        self.selected_saved_exercise_source_file = exercise.source_material_filename
        self.selected_saved_concepts = concept_details

    @rx.event
    def delete_saved_exercise(self, exercise_id: int | None):
        """Delete a saved Beta AI exercise and reload the saved list."""
        if exercise_id is None:
            return

        with rx.session() as session:
            exercise = session.get(BetaExercise, exercise_id)
            if exercise is None:
                return rx.toast.error(
                    description="Beta AI exercise not found.",
                    duration=5000,
                    position="bottom-center",
                    invert=True,
                )
            session.delete(exercise)
            session.commit()

        if self.selected_saved_exercise_id == exercise_id:
            self.clear_selected_saved_exercise()
        self.load_beta_exercises()
        return rx.toast.success(
            description="Beta AI exercise deleted.",
            duration=5000,
            position="bottom-center",
            invert=True,
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
                    text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                text_parts.append(" ".join(text.replace("\n", " ").split()))
                file_names.append(file.name or "<unnamed file>")

            self.source_material_text = "\n\n".join(text_parts)
            self.source_material_filename = ", ".join(file_names)
        except Exception as exc:
            self.extracting_source_material = False
            yield rx.toast.error(
                description=f"Failed to extract PDF text: {exc}",
                duration=5000,
                position="bottom-center",
                invert=True,
            )
            return

        self.extracting_source_material = False
        yield rx.toast.success(
            description="PDF text extracted.",
            duration=5000,
            position="bottom-center",
            invert=True,
        )

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
            concept_target_count = self.concept_target_count
            core_point_target_count = self.core_point_target_count
            misconception_target_count = self.misconception_target_count
        yield

        try:
            response = await generate_concepts_from_material(
                title=title,
                description=description,
                source_material_text=source_material_text,
                concept_target_count=concept_target_count,
                core_point_target_count=core_point_target_count,
                misconception_target_count=misconception_target_count,
            )
        except Exception as exc:
            async with self:
                self.generating_concepts = False
            yield rx.toast.error(
                description=f"Concept generation failed: {exc}",
                duration=5000,
                position="bottom-center",
                invert=True,
            )
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
        yield rx.toast.success(
            description="Concepts generated. Please review them before saving.",
            duration=5000,
            position="bottom-center",
            invert=True,
        )

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
            return rx.toast.error(
                description="Please generate or add at least one concept first.",
                duration=5000,
                position="bottom-center",
                invert=True,
            )

        title = self.title.strip()
        validation_error = self._validate_generated_concepts()
        if validation_error:
            return rx.toast.error(
                description=validation_error,
                duration=5000,
                position="bottom-center",
                invert=True,
            )

        if self._beta_exercise_title_exists(title):
            return rx.toast.error(
                description=(
                    "A Beta AI exercise with this title already exists. "
                    "Please choose a different title."
                ),
                duration=5000,
                position="bottom-center",
                invert=True,
            )

        self.saving_exercise = True
        try:
            with rx.session() as session:
                exercise = BetaExercise(
                    title=title,
                    description=self.description.strip(),
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
                        concept_id=concept.concept_id.strip(),
                        label=concept.label.strip(),
                        description=concept.description.strip(),
                        order_index=concept_index,
                    )
                    session.add(db_concept)
                    session.flush()
                    if db_concept.id is None:
                        raise ValueError("Failed to create beta concept id.")

                    for core_point_index, core_point in enumerate(concept.core_points):
                        core_point_text = core_point.text.strip()
                        if core_point_text:
                            session.add(
                                BetaCorePoint(
                                    beta_concept_id=db_concept.id,
                                    text=core_point_text,
                                    required=core_point.required,
                                    order_index=core_point_index,
                                )
                            )

                    for misconception_index, misconception in enumerate(
                        concept.misconceptions
                    ):
                        misconception_label = misconception.label.strip()
                        if misconception_label:
                            session.add(
                                BetaMisconception(
                                    beta_concept_id=db_concept.id,
                                    label=misconception_label,
                                    order_index=misconception_index,
                                )
                            )

                session.commit()
        except Exception as exc:
            self.saving_exercise = False
            return rx.toast.error(
                description=f"Failed to save Beta AI exercise: {exc}",
                duration=5000,
                position="bottom-center",
                invert=True,
            )

        self.saving_exercise = False
        self.reset_builder()
        self.load_beta_exercises()
        return rx.toast.success(
            description="Beta AI exercise saved.",
            duration=5000,
            position="bottom-center",
            invert=True,
        )
