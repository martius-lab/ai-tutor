"""State for the Beta AI builder in lecture exercise management."""

import io
from collections.abc import Mapping
from datetime import datetime

import pdfplumber
import reflex as rx
from sqlalchemy.orm import selectinload
from sqlmodel import Session, SQLModel, col, func, select

from aitutor import routes
from aitutor.auth.protection import state_has_lecture_role, state_require_lecture_role
from aitutor.auth.state import SessionState
from aitutor.beta_ai.concept_generation import generate_concepts_from_material
from aitutor.beta_ai.schemas import (
    EditableConcept,
    EditableCorePoint,
    EditableMisconception,
)
from aitutor.language_state import BackendTranslations as BT
from aitutor.models import (
    BetaConcept,
    BetaCorePoint,
    BetaExercise,
    BetaExerciseResult,
    BetaMisconception,
    LectureRole,
    Tag,
)
from aitutor.pages.lecture_manage_exercises.state import (
    LECTURE_MANAGE_EXERCISES_FIELD_MAX_LENGTHS,
)

SECONDS_PER_ESTIMATED_QUESTION = 90


class BetaAIExercisesState(SessionState):
    """State for the UI-first Beta AI exercise builder."""

    MIN_GENERATION_TARGET: int = 1
    MAX_CONCEPT_TARGET: int = 30
    MAX_CORE_POINT_TARGET: int = 15
    MAX_MISCONCEPTION_TARGET: int = 10

    current_lecture_id: int | None = None
    title: str = ""
    description: str = ""
    concept_target_count: int = 8
    core_point_target_count: int = 4
    misconception_target_count: int = 2
    source_material_text: str = ""
    source_material_filename: str = ""
    generated_concepts: list[EditableConcept] = []
    extracting_source_material: bool = False
    generating_concepts: bool = False
    saving_exercise: bool = False
    editing_exercise_id: int | None = None
    is_hidden: bool = False
    deadline: str = ""
    days_to_complete: str = ""
    use_deadline: bool = True
    exercise_has_started: bool = False
    builder_dialog_is_open: bool = False
    metadata_info_dialog_is_open: bool = False
    tag_names: list[str] = []
    selected_tags: list[str] = []
    new_tag_name: str = ""
    add_tag_dialog_is_open: bool = False

    @rx.event
    def set_metadata_info_dialog_is_open(self, value: bool):
        """Synchronize dismissal by Escape or the dialog overlay."""
        self.metadata_info_dialog_is_open = value

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def set_new_tag_name(self, value: str):
        """Set the name used by the add-tag dialog."""
        self.new_tag_name = value[:100]

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def set_add_tag_dialog_is_open(self, is_open: bool):
        """Set whether the add-tag dialog is open."""
        self.add_tag_dialog_is_open = is_open
        if not is_open:
            self.new_tag_name = ""

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def set_title(self, value: str):
        """Set beta exercise title."""
        self.title = value[: LECTURE_MANAGE_EXERCISES_FIELD_MAX_LENGTHS["title"]]

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def set_description(self, value: str):
        """Set beta exercise description."""
        self.description = value[
            : LECTURE_MANAGE_EXERCISES_FIELD_MAX_LENGTHS["description"]
        ]

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def set_is_hidden(self, value: bool):
        """Set whether the exercise is hidden from students."""
        self.is_hidden = value

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def set_deadline(self, value: str):
        """Set the exercise deadline."""
        self.deadline = value

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def set_days_to_complete(self, value: str):
        """Set the number of days available for the exercise."""
        self.days_to_complete = value[
            : LECTURE_MANAGE_EXERCISES_FIELD_MAX_LENGTHS["days_to_complete"]
        ]

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def set_use_deadline(self, value: bool):
        """Set whether this exercise uses a deadline."""
        self.use_deadline = value

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def set_concept_target_count(self, value: str):
        """Set the approximate number of concepts to generate."""
        self._set_generation_target(
            "concept_target_count", value, self.MAX_CONCEPT_TARGET
        )

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def set_core_point_target_count(self, value: str):
        """Set the approximate number of core points per concept."""
        self._set_generation_target(
            "core_point_target_count", value, self.MAX_CORE_POINT_TARGET
        )

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def set_misconception_target_count(self, value: str):
        """Set the approximate number of misconceptions per concept."""
        self._set_generation_target(
            "misconception_target_count", value, self.MAX_MISCONCEPTION_TARGET
        )

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def set_concept_label(self, concept_index: int, value: str):
        """Set concept label."""
        self.generated_concepts[concept_index].label = value

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def set_concept_description(self, concept_index: int, value: str):
        """Set concept description."""
        self.generated_concepts[concept_index].description = value

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def set_core_point_text(
        self, concept_index: int, core_point_index: int, value: str
    ):
        """Set core point text."""
        self.generated_concepts[concept_index].core_points[
            core_point_index
        ].text = value

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def set_misconception_label(
        self, concept_index: int, misconception_index: int, value: str
    ):
        """Set misconception label."""
        self.generated_concepts[concept_index].misconceptions[
            misconception_index
        ].label = value

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def set_builder_dialog_is_open(self, is_open: bool):
        """Set whether the Beta AI builder dialog is open."""
        self.builder_dialog_is_open = is_open

    @rx.var
    def selectable_tags(self) -> list[str]:
        """Return lecture tags that are not selected yet."""
        return [tag for tag in self.tag_names if tag not in self.selected_tags]

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
            and not self.exercise_has_started
        )

    @rx.var
    def estimated_question_count(self) -> int:
        """Estimate one question per filled core point plus two per concept."""
        question_count = 0
        for concept in self.generated_concepts:
            core_point_count = sum(
                bool(point.text.strip()) for point in concept.core_points
            )
            if core_point_count:
                question_count += core_point_count + 2
        return question_count

    @rx.var
    def estimated_duration_minutes(self) -> int:
        """Round the planning estimate up to whole minutes."""
        seconds = self.estimated_question_count * SECONDS_PER_ESTIMATED_QUESTION
        return (seconds + 59) // 60

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
    def is_editing(self) -> bool:
        """Whether the builder is editing an existing exercise."""
        return self.editing_exercise_id is not None

    @rx.event
    def open_metadata_info_dialog(self):
        """Open the authoring guide using the app's controlled-dialog pattern."""
        self.metadata_info_dialog_is_open = True

    @rx.event
    def close_metadata_info_dialog(self):
        """Close the authoring guide from either close button."""
        self.metadata_info_dialog_is_open = False

    def _matches_lecture_route(self, lecture_id: int | None) -> bool:
        """Keep builder operations scoped to the authorized route lecture."""
        try:
            route_lecture_id = self.get_route_param_or_error("lecture_id", dtype=int)
        except KeyError, ValueError, TypeError:
            return False
        return lecture_id is not None and lecture_id == route_lecture_id

    def load_tags(self):
        """Load the shared tags belonging to the current lecture."""
        if self.current_lecture_id is None:
            self.tag_names = []
            return
        with rx.session() as session:
            self.tag_names = list(
                session.exec(
                    select(Tag.name)
                    .where(Tag.lecture_id == self.current_lecture_id)
                    .order_by(func.lower(Tag.name))
                ).all()
            )

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def add_to_selected_tags(self, tag: str):
        """Add one lecture tag to the Beta AI exercise."""
        if tag and tag not in self.selected_tags:
            self.selected_tags.append(tag)

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def remove_selected_tag(self, tag: str):
        """Remove one selected tag."""
        if tag in self.selected_tags:
            self.selected_tags.remove(tag)

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def add_new_tag(self):
        """Create a shared lecture tag and select it for this exercise."""
        if not self._matches_lecture_route(self.current_lecture_id):
            return rx.redirect(routes.MY_LECTURES)
        tag_name = self.new_tag_name[:100]
        if not tag_name:
            return rx.window_alert("Please enter a tag name.")
        with rx.session() as session:
            existing_tag = session.exec(
                select(Tag).where(
                    Tag.name == tag_name,
                    Tag.lecture_id == self.current_lecture_id,
                )
            ).one_or_none()
            if existing_tag is not None:
                return rx.window_alert("Tag exists already.")
            session.add(Tag(name=tag_name, lecture_id=self.current_lecture_id))
            session.commit()
        self.load_tags()
        self.add_to_selected_tags(tag_name)
        self.add_tag_dialog_is_open = False
        self.new_tag_name = ""
        return rx.toast.success(
            BT.tag_was_added(self.language),
            duration=2500,
            position="bottom-center",
            invert=True,
        )

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
            return BT.beta_ai_generate_concept_first(self.language)

        for concept_index, concept in enumerate(self.generated_concepts, start=1):
            if not concept.label.strip():
                return BT.beta_ai_concept_label_required(self.language, concept_index)

            has_core_point = any(
                core_point.text.strip() for core_point in concept.core_points
            )
            if not has_core_point:
                return BT.beta_ai_core_point_required(self.language, concept_index)

            for misconception_index, misconception in enumerate(
                concept.misconceptions, start=1
            ):
                if not misconception.label.strip():
                    return BT.beta_ai_misconception_label_required(
                        self.language, concept_index, misconception_index
                    )

        return None

    def _beta_exercise_title_exists(self, title: str) -> bool:
        """Return whether the title exists in the current lecture."""
        if self.current_lecture_id is None:
            return False
        with rx.session() as session:
            query = select(BetaExercise).where(
                BetaExercise.lecture_id == self.current_lecture_id,
                BetaExercise.title == title,
            )
            if self.editing_exercise_id is not None:
                query = query.where(BetaExercise.id != self.editing_exercise_id)
            existing_exercise = session.exec(query).first()
        return existing_exercise is not None

    def _deadline_values(self) -> tuple[datetime | None, int | None] | None:
        """Return validated deadline values or None when required values are missing."""
        if not self.use_deadline:
            return None, None
        if not self.deadline or not self.days_to_complete:
            return None
        return datetime.fromisoformat(self.deadline), int(self.days_to_complete)

    def _exercise_has_results(self, session: Session, exercise_id: int) -> bool:
        """Check whether a student has started the exercise."""
        return (
            session.exec(
                select(BetaExerciseResult).where(
                    BetaExerciseResult.beta_exercise_id == exercise_id
                )
            ).first()
            is not None
        )

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
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
        self.editing_exercise_id = None
        self.is_hidden = False
        self.deadline = ""
        self.days_to_complete = ""
        self.use_deadline = True
        self.exercise_has_started = False
        self.selected_tags = []
        self.new_tag_name = ""
        self.add_tag_dialog_is_open = False

    def _prepare_builder_for_lecture(self, lecture_id: int) -> None:
        """Reset the builder and load the selected lecture's tags."""
        self.current_lecture_id = lecture_id
        self.reset_builder()
        self.load_tags()

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def open_builder_dialog(self, lecture_id: int | None):
        """Open a blank Beta AI builder for the selected lecture."""
        if lecture_id is None or not self._matches_lecture_route(lecture_id):
            return rx.redirect(routes.MY_LECTURES)
        self._prepare_builder_for_lecture(lecture_id)
        self.builder_dialog_is_open = True

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def open_builder_dialog_for_editing(
        self, lecture_id: int | None, exercise_id: int | None
    ):
        """Open an existing Beta AI exercise in the builder dialog."""
        if (
            lecture_id is None
            or exercise_id is None
            or not self._matches_lecture_route(lecture_id)
        ):
            return rx.redirect(routes.MY_LECTURES)
        self._prepare_builder_for_lecture(lecture_id)
        result = self.load_exercise_for_editing(exercise_id)
        if result is not None:
            return result
        self.builder_dialog_is_open = True

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def close_builder_dialog(self):
        """Close the Beta AI builder dialog."""
        self.builder_dialog_is_open = False

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def cancel_builder(self):
        """Reset the builder and return to the shared exercise management page."""
        self.reset_builder()
        if self.current_lecture_id is None:
            return rx.redirect(routes.MY_LECTURES)
        return rx.redirect(
            f"{routes.LECTURE_MANAGE_EXERCISES}/{self.current_lecture_id}"
        )

    def _load_editable_concepts(
        self, session: Session, concepts: list[BetaConcept]
    ) -> list[EditableConcept]:
        """Load the persisted concept hierarchy into builder editor models."""
        editable_concepts = []
        for concept in concepts:
            assert concept.id is not None, "Persisted Beta AI concept has no ID."
            editable_concepts.append(
                self._load_editable_concept(session, concept, concept.id)
            )
        return editable_concepts

    def _load_editable_concept(
        self, session: Session, concept: BetaConcept, concept_id: int
    ) -> EditableConcept:
        """Load the ordered core points and misconceptions for one concept."""
        core_points = list(
            session.exec(
                select(BetaCorePoint)
                .where(BetaCorePoint.beta_concept_id == concept_id)
                .order_by(col(BetaCorePoint.order_index))
            ).all()
        )
        misconceptions = list(
            session.exec(
                select(BetaMisconception)
                .where(BetaMisconception.beta_concept_id == concept_id)
                .order_by(col(BetaMisconception.order_index))
            ).all()
        )
        return EditableConcept(
            id=concept.id,
            concept_id=concept.concept_id,
            label=concept.label,
            description=concept.description,
            core_points=[
                EditableCorePoint(
                    id=core_point.id,
                    text=core_point.text,
                )
                for core_point in core_points
            ],
            misconceptions=[
                EditableMisconception(
                    id=misconception.id,
                    label=misconception.label,
                )
                for misconception in misconceptions
            ],
        )

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def load_exercise_for_editing(self, exercise_id: int):
        """Load one Beta AI exercise into the existing builder."""
        if not self._matches_lecture_route(self.current_lecture_id):
            return rx.redirect(routes.NOT_FOUND)
        with rx.session() as session:
            exercise = session.exec(
                select(BetaExercise)
                .options(selectinload(BetaExercise.tags))  # type: ignore
                .where(BetaExercise.id == exercise_id)
            ).one_or_none()
            if exercise is None or exercise.lecture_id != self.current_lecture_id:
                return rx.redirect(routes.NOT_FOUND)

            concepts = list(
                session.exec(
                    select(BetaConcept)
                    .where(BetaConcept.beta_exercise_id == exercise_id)
                    .order_by(col(BetaConcept.order_index))
                ).all()
            )
            exercise_has_started = self._exercise_has_results(session, exercise_id)
            editable_concepts = self._load_editable_concepts(session, concepts)

        self.editing_exercise_id = exercise_id
        self.title = exercise.title
        self.description = exercise.description
        self.source_material_text = exercise.source_material_text
        self.source_material_filename = exercise.source_material_filename
        self.generated_concepts = editable_concepts
        self.is_hidden = exercise.is_hidden
        self.deadline = (
            exercise.deadline.strftime("%Y-%m-%dT%H:%M") if exercise.deadline else ""
        )
        self.days_to_complete = (
            str(exercise.days_to_complete) if exercise.days_to_complete else ""
        )
        self.use_deadline = (
            exercise.deadline is not None and exercise.days_to_complete is not None
        )
        self.exercise_has_started = exercise_has_started
        self.selected_tags = [tag.name for tag in exercise.tags]

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
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
                file_names.append(file.name or BT.beta_ai_unnamed_file(self.language))

            self.source_material_text = "\n\n".join(text_parts)
            self.source_material_filename = ", ".join(file_names)
        except Exception as exc:
            self.extracting_source_material = False
            yield rx.toast.error(
                description=BT.beta_ai_pdf_extraction_failed(self.language, exc),
                duration=5000,
                position="bottom-center",
                invert=True,
            )
            return

        self.extracting_source_material = False
        yield rx.toast.success(
            description=BT.beta_ai_pdf_extracted(self.language),
            duration=5000,
            position="bottom-center",
            invert=True,
        )

    @rx.event(background=True)
    async def generate_concepts(self):
        """Generate editable concepts from the current source material."""
        async with self:
            if not state_has_lecture_role(self, LectureRole.OWNER):
                return
            if not self._matches_lecture_route(self.current_lecture_id):
                return
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
                error_message = BT.beta_ai_generation_failed(self.language, exc)
            yield rx.toast.error(
                description=error_message,
                duration=5000,
                position="bottom-center",
                invert=True,
            )
            return

        async with self:
            if not self._matches_lecture_route(self.current_lecture_id):
                self.generating_concepts = False
                return
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
            success_message = BT.beta_ai_concepts_generated(self.language)
        yield rx.toast.success(
            description=success_message,
            duration=5000,
            position="bottom-center",
            invert=True,
        )

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def add_concept(self):
        """Add an empty concept manually."""
        self.generated_concepts.append(
            EditableConcept(
                concept_id=f"manual.concept-{len(self.generated_concepts) + 1}",
                label=BT.beta_ai_new_concept(self.language),
                core_points=[EditableCorePoint()],
            )
        )

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def delete_concept(self, concept_index: int):
        """Delete a concept."""
        del self.generated_concepts[concept_index]

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def add_core_point(self, concept_index: int):
        """Add a core point."""
        self.generated_concepts[concept_index].core_points.append(EditableCorePoint())

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def delete_core_point(self, concept_index: int, core_point_index: int):
        """Delete a core point."""
        del self.generated_concepts[concept_index].core_points[core_point_index]

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def add_misconception(self, concept_index: int):
        """Add a misconception."""
        self.generated_concepts[concept_index].misconceptions.append(
            EditableMisconception()
        )

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def delete_misconception(self, concept_index: int, misconception_index: int):
        """Delete a misconception."""
        del self.generated_concepts[concept_index].misconceptions[misconception_index]

    @staticmethod
    def _delete_removed_rows(
        session: Session, existing: Mapping[int, SQLModel], retained_ids: set[int]
    ) -> None:
        """Delete persisted builder items that are no longer in the editor."""
        for row_id, row in existing.items():
            if row_id not in retained_ids:
                session.delete(row)

    def _save_concepts(self, session, exercise_id: int):
        """Create or update the editable concept hierarchy."""
        existing_concepts = {
            concept.id: concept
            for concept in session.exec(
                select(BetaConcept).where(BetaConcept.beta_exercise_id == exercise_id)
            ).all()
            if concept.id is not None
        }
        retained_concept_ids = {
            concept.id for concept in self.generated_concepts if concept.id is not None
        }
        self._delete_removed_rows(session, existing_concepts, retained_concept_ids)

        for concept_index, concept in enumerate(self.generated_concepts):
            db_concept = existing_concepts.get(concept.id)
            if db_concept is None:
                db_concept = BetaConcept(beta_exercise_id=exercise_id)
            db_concept.concept_id = concept.concept_id.strip()
            db_concept.label = concept.label.strip()
            db_concept.description = concept.description.strip()
            db_concept.order_index = concept_index
            session.add(db_concept)
            session.flush()
            if db_concept.id is None:
                raise ValueError("Failed to create beta concept id.")
            self._save_core_points(session, db_concept.id, concept)
            self._save_misconceptions(session, db_concept.id, concept)

    def _save_core_points(self, session, concept_id: int, concept: EditableConcept):
        """Create, update, or delete core points for one concept."""
        existing = {
            core_point.id: core_point
            for core_point in session.exec(
                select(BetaCorePoint).where(BetaCorePoint.beta_concept_id == concept_id)
            ).all()
            if core_point.id is not None
        }
        retained_ids = {
            core_point.id
            for core_point in concept.core_points
            if core_point.id is not None and core_point.text.strip()
        }
        self._delete_removed_rows(session, existing, retained_ids)

        for order_index, core_point in enumerate(concept.core_points):
            if not core_point.text.strip():
                continue
            db_core_point = existing.get(core_point.id)
            if db_core_point is None:
                db_core_point = BetaCorePoint(beta_concept_id=concept_id)
            db_core_point.text = core_point.text.strip()
            db_core_point.order_index = order_index
            session.add(db_core_point)

    def _save_misconceptions(self, session, concept_id: int, concept: EditableConcept):
        """Create, update, or delete misconceptions for one concept."""
        existing = {
            misconception.id: misconception
            for misconception in session.exec(
                select(BetaMisconception).where(
                    BetaMisconception.beta_concept_id == concept_id
                )
            ).all()
            if misconception.id is not None
        }
        retained_ids = {
            misconception.id
            for misconception in concept.misconceptions
            if misconception.id is not None
        }
        self._delete_removed_rows(session, existing, retained_ids)

        for order_index, misconception in enumerate(concept.misconceptions):
            if not misconception.label.strip():
                continue
            db_misconception = existing.get(misconception.id)
            if db_misconception is None:
                db_misconception = BetaMisconception(beta_concept_id=concept_id)
            db_misconception.label = misconception.label.strip()
            db_misconception.order_index = order_index
            session.add(db_misconception)

    @rx.event
    @state_require_lecture_role(LectureRole.OWNER)
    def save_beta_exercise(self):
        """Persist the exercise and reviewed concepts."""
        if not self._matches_lecture_route(self.current_lecture_id):
            return rx.redirect(routes.MY_LECTURES)
        if not self.can_save_exercise:
            return rx.toast.error(
                description=BT.beta_ai_generate_concept_first(self.language),
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
                description=BT.beta_ai_title_exists(self.language),
                duration=5000,
                position="bottom-center",
                invert=True,
            )

        deadline_values = self._deadline_values()
        if deadline_values is None:
            return rx.window_alert("Please enter both a deadline and days to complete.")
        deadline, days_to_complete = deadline_values

        self.saving_exercise = True
        try:
            with rx.session() as session:
                if self.editing_exercise_id is None:
                    exercise = BetaExercise(lecture_id=self.current_lecture_id)
                else:
                    exercise = session.get(BetaExercise, self.editing_exercise_id)
                    if (
                        exercise is None
                        or exercise.lecture_id != self.current_lecture_id
                    ):
                        return rx.redirect(routes.NOT_FOUND)
                    if (
                        self._exercise_has_results(session, self.editing_exercise_id)
                        and not self.exercise_has_started
                    ):
                        return rx.toast.error(
                            description=BT.beta_ai_started_while_editing(self.language),
                            duration=5000,
                            position="bottom-center",
                            invert=True,
                        )
                exercise.title = title
                if not self.exercise_has_started:
                    exercise.description = self.description.strip()
                    exercise.source_material_text = self.source_material_text
                    exercise.source_material_filename = self.source_material_filename
                exercise.is_hidden = self.is_hidden
                exercise.tags = list(
                    session.exec(
                        select(Tag).where(
                            Tag.lecture_id == self.current_lecture_id,
                            Tag.name.in_(self.selected_tags),  # type: ignore
                        )
                    ).all()
                )
                exercise.deadline = deadline
                exercise.days_to_complete = days_to_complete
                session.add(exercise)
                session.flush()
                if exercise.id is None:
                    raise ValueError("Failed to create beta exercise id.")
                if not self.exercise_has_started:
                    self._save_concepts(session, exercise.id)
                session.commit()
        except Exception as exc:
            return rx.toast.error(
                description=BT.beta_ai_save_failed(self.language, exc),
                duration=5000,
                position="bottom-center",
                invert=True,
            )
        finally:
            self.saving_exercise = False

        self.builder_dialog_is_open = False
        self.reset_builder()
        return [
            rx.toast.success(
                description=BT.beta_ai_exercise_saved(self.language),
                duration=5000,
                position="bottom-center",
                invert=True,
            ),
            rx.redirect(f"{routes.LECTURE_MANAGE_EXERCISES}/{self.current_lecture_id}"),
        ]
