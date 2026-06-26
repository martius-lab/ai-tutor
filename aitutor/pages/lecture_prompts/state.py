"""State for the lecture-specific prompts page."""

import reflex as rx
from sqlalchemy.exc import IntegrityError
from sqlmodel import or_, select

import aitutor.routes as routes
from aitutor.auth.protection import state_require_role_or_permission
from aitutor.auth.state import SessionState
from aitutor.language_state import BackendTranslations as BT
from aitutor.models import Exercise, Lecture, Prompt, UserRole
from aitutor.utilities.lecture_permissions import user_may_manage_lecture_exercises


class LectureManagePromptsState(SessionState):
    """State for managing prompts visible inside one lecture."""

    current_lecture_id: int | None = None
    current_default_prompt_id: int | None = None
    unsaved_changes: bool = False
    prompts: dict[int | None, Prompt] = {}
    replacement_prompt_id: str = ""
    prompt_to_delete_id: int | None = None
    new_prompt_name: str = ""
    new_prompt_template: str = ""
    add_prompt_dialog_open: bool = False

    @rx.event
    def set_prompt_name(self, prompt_id: int | None, name: str):
        """Set the name of a lecture-specific prompt."""
        if prompt_id in self.prompts and self._is_lecture_prompt(self.prompts[prompt_id]):
            self.prompts[prompt_id].name = name
            self.unsaved_changes = True

    @rx.event
    def set_prompt_template(self, prompt_id: int | None, template: str):
        """Set the template of a lecture-specific prompt."""
        if prompt_id in self.prompts and self._is_lecture_prompt(self.prompts[prompt_id]):
            self.prompts[prompt_id].prompt_template = template
            self.unsaved_changes = True

    @rx.event
    def set_replacement_prompt_id(self, prompt_id: str):
        """Set the replacement prompt."""
        self.replacement_prompt_id = prompt_id

    @rx.event
    def set_prompt_to_delete(self, prompt_id: int | None):
        """Set the prompt to delete."""
        self.prompt_to_delete_id = prompt_id

    @rx.event
    def set_new_prompt_name(self, name: str):
        """Set the name for the new lecture-specific prompt."""
        self.new_prompt_name = name

    @rx.event
    def set_new_prompt(self, prompt: str):
        """Set the template for the new lecture-specific prompt."""
        self.new_prompt_template = prompt

    @rx.event
    def set_add_prompt_dialog_open(self, is_open: bool):
        """Set whether the add prompt dialog is open."""
        self.add_prompt_dialog_open = is_open

    @rx.event
    def set_default_prompt(self, prompt_id: int | None):
        """Set the lecture default prompt."""
        if prompt_id is None or prompt_id not in self.prompts:
            return
        self.current_default_prompt_id = prompt_id
        self.unsaved_changes = True

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.STUDENT)
    def on_load(self):
        """Initialize the page for one lecture."""
        self.global_load()
        self.current_lecture_id = None
        self.current_default_prompt_id = None
        self.prompts = {}

        try:
            lecture_id = int(self.lecture_id)
        except ValueError:
            return rx.redirect(routes.NOT_FOUND)

        if not self._user_may_manage_lecture(lecture_id):
            return rx.redirect(routes.MY_LECTURES)

        with rx.session() as session:
            lecture = session.get(Lecture, lecture_id)
            if lecture is None:
                return rx.redirect(routes.NOT_FOUND)
            self.current_default_prompt_id = lecture.default_prompt_id

        self.current_lecture_id = lecture_id
        self.load_prompts_from_db()

    def on_logout(self):
        """Clear state when the user logs out."""
        self.current_lecture_id = None
        self.current_default_prompt_id = None
        self.unsaved_changes = False
        self.prompts = {}
        self.replacement_prompt_id = ""
        self.prompt_to_delete_id = None
        self.new_prompt_name = ""
        self.new_prompt_template = ""
        self.add_prompt_dialog_open = False

    def _user_may_manage_lecture(self, lecture_id: int) -> bool:
        """Return whether the current user may manage prompts in this lecture."""
        if self.authenticated_user is None or self.authenticated_user.id is None:
            return False

        with rx.session() as session:
            return user_may_manage_lecture_exercises(
                session,
                user_id=self.authenticated_user.id,
                global_permissions=self.global_permissions,
                lecture_id=lecture_id,
            )

    def _is_lecture_prompt(self, prompt: Prompt) -> bool:
        """Return whether the prompt belongs to the currently loaded lecture."""
        return (
            self.current_lecture_id is not None
            and prompt.lecture_id == self.current_lecture_id
        )

    def _remaining_prompt_options(self, *, global_prompts: bool) -> list[dict[str, str]]:
        """Return serializable replacement prompt options."""
        return [
            {
                "id": str(prompt.id),
                "name": prompt.name,
            }
            for prompt in self.prompts.values()
            if prompt.id is not None
            and prompt.id != self.prompt_to_delete_id
            and prompt.name != ""
            and (prompt.lecture_id is None) == global_prompts
        ]

    @rx.var
    def remaining_local_prompts(self) -> list[dict[str, str]]:
        """Return available local replacement prompts excluding the one to delete."""
        return self._remaining_prompt_options(global_prompts=False)

    @rx.var
    def remaining_global_prompts(self) -> list[dict[str, str]]:
        """Return available global replacement prompts excluding the one to delete."""
        return self._remaining_prompt_options(global_prompts=True)

    def names_are_unique(self, names: list[str]) -> bool:
        """Check if all names in the list are unique."""
        return len(names) == len(set(names))

    def _lecture_prompt_names(self) -> list[str]:
        """Return local prompt names for the current lecture."""
        return [
            prompt.name for prompt in self.prompts.values() if self._is_lecture_prompt(prompt)
        ]

    def _names_conflict_with_db(self, prompt_ids: set[int | None], names: list[str]) -> bool:
        """Return whether any name conflicts with local prompts in this lecture."""
        if self.current_lecture_id is None:
            return False

        with rx.session() as session:
            db_prompts = session.exec(
                select(Prompt).where(
                    Prompt.lecture_id == self.current_lecture_id,
                )
            ).all()
        return any(
            prompt.id not in prompt_ids and prompt.name in names for prompt in db_prompts
        )

    @rx.event
    def save_prompts_to_db(self):
        """Save lecture-specific prompt edits to the database."""
        lecture_prompts = {
            prompt_id: prompt
            for prompt_id, prompt in self.prompts.items()
            if self._is_lecture_prompt(prompt)
        }
        local_names = [prompt.name for prompt in lecture_prompts.values()]
        if not self.names_are_unique(local_names):
            yield rx.toast.error(
                description=BT.prompt_names_unique_error(self.language),
                duration=5000,
                position="bottom-center",
                invert=True,
            )
            return
        if self._names_conflict_with_db(
            set(lecture_prompts.keys()),
            [prompt.name for prompt in lecture_prompts.values()],
        ):
            yield rx.toast.error(
                description=BT.prompt_names_unique_error(self.language),
                duration=5000,
                position="bottom-center",
                invert=True,
            )
            return
        if "" in [prompt.name for prompt in lecture_prompts.values()]:
            yield rx.toast.error(
                description=BT.prompt_names_nonempty_error(self.language),
                duration=5000,
                position="bottom-center",
                invert=True,
            )
            return

        try:
            with rx.session() as session:
                session.add_all(lecture_prompts.values())
                if self.current_lecture_id is not None:
                    lecture = session.get(Lecture, self.current_lecture_id)
                    if lecture is not None:
                        lecture.default_prompt_id = self.current_default_prompt_id
                        session.add(lecture)
                session.commit()
        except IntegrityError:
            yield rx.toast.error(
                description=BT.prompt_names_unique_error(self.language),
                duration=5000,
                position="bottom-center",
                invert=True,
            )
            return

        self.unsaved_changes = False
        self.load_prompts_from_db()

        yield rx.toast.success(
            description=BT.prompts_saved(self.language),
            duration=5000,
            position="bottom-center",
            invert=True,
        )

    @rx.event
    def delete_prompt(self, prompt_id: int | None):
        """Delete a lecture-specific prompt from the database."""
        if prompt_id is None or self.current_lecture_id is None:
            return

        with rx.session() as session:
            prompt = session.get(Prompt, prompt_id)
            if prompt is None or prompt.lecture_id != self.current_lecture_id:
                yield rx.toast.error(
                    description=BT.invalid_replacement_prompt(self.language),
                    duration=5000,
                    position="bottom-center",
                    invert=True,
                )
                return

            try:
                replacement_prompt_id = int(self.replacement_prompt_id)
            except ValueError:
                replacement_prompt_id = None

            replacement_prompt = (
                session.get(Prompt, replacement_prompt_id)
                if replacement_prompt_id is not None
                else None
            )

            if not replacement_prompt or not (
                replacement_prompt.lecture_id is None
                or replacement_prompt.lecture_id == self.current_lecture_id
            ):
                yield rx.toast.error(
                    description=BT.replacement_prompt_not_found(self.language),
                    duration=5000,
                    position="bottom-center",
                    invert=True,
                )
                return

            if replacement_prompt.id == prompt_id:
                yield rx.toast.error(
                    description=BT.invalid_replacement_prompt(self.language),
                    duration=5000,
                    position="bottom-center",
                    invert=True,
                )
                return

            exercises = session.exec(
                select(Exercise).where(
                    Exercise.prompt_id == prompt_id,
                    Exercise.lecture_id == self.current_lecture_id,
                )
            ).all()

            for exercise in exercises:
                exercise.prompt_id = replacement_prompt.id
                session.add(exercise)

            lecture = session.get(Lecture, self.current_lecture_id)
            if lecture is not None and lecture.default_prompt_id == prompt_id:
                lecture.default_prompt_id = replacement_prompt.id
                self.current_default_prompt_id = replacement_prompt.id
                session.add(lecture)

            session.delete(prompt)
            session.commit()

        if prompt_id in self.prompts:
            del self.prompts[prompt_id]
            yield rx.toast.success(
                description=BT.prompt_deleted(self.language),
                duration=5000,
                position="bottom-center",
                invert=True,
            )
        self.replacement_prompt_id = ""
        self.prompt_to_delete_id = None
        self.load_prompts_from_db()

    @rx.event
    def add_prompt(self):
        """Add a new lecture-specific prompt."""
        if self.current_lecture_id is None:
            return rx.redirect(routes.MY_LECTURES)

        if not self.names_are_unique(self._lecture_prompt_names() + [self.new_prompt_name]):
            yield rx.toast.error(
                description=BT.prompt_names_unique_error(self.language),
                duration=5000,
                position="bottom-center",
                invert=True,
            )
            return
        with rx.session() as session:
            existing_prompt = session.exec(
                select(Prompt).where(
                    Prompt.name == self.new_prompt_name,
                    Prompt.lecture_id == self.current_lecture_id,
                )
            ).first()
        if existing_prompt is not None:
            yield rx.toast.error(
                description=BT.prompt_names_unique_error(self.language),
                duration=5000,
                position="bottom-center",
                invert=True,
            )
            return
        if self.new_prompt_name == "":
            yield rx.toast.error(
                description=BT.prompt_names_nonempty_error(self.language),
                duration=5000,
                position="bottom-center",
                invert=True,
            )
            return

        try:
            with rx.session() as session:
                new_prompt = Prompt(
                    name=self.new_prompt_name,
                    prompt_template=self.new_prompt_template,
                    lecture_id=self.current_lecture_id,
                )
                session.add(new_prompt)
                session.commit()
                session.refresh(new_prompt)
                if new_prompt.id:
                    self.prompts[new_prompt.id] = new_prompt
        except IntegrityError:
            yield rx.toast.error(
                description=BT.prompt_names_unique_error(self.language),
                duration=5000,
                position="bottom-center",
                invert=True,
            )
            return

        self.new_prompt_name = ""
        self.new_prompt_template = ""
        self.add_prompt_dialog_open = False
        yield rx.toast.success(
            description=BT.prompt_added(self.language),
            duration=5000,
            position="bottom-center",
            invert=True,
        )

    @rx.event
    def load_prompts_from_db(self):
        """Load global and lecture-specific prompts from the database."""
        if self.current_lecture_id is None:
            self.prompts = {}
            self.unsaved_changes = False
            return

        with rx.session() as session:
            prompts = session.exec(
                select(Prompt)
                .where(
                    or_(
                        Prompt.lecture_id == None,  # noqa: E711
                        Prompt.lecture_id == self.current_lecture_id,
                    )
                )
                .order_by(
                    Prompt.is_default_prompt.desc(),  # type: ignore
                    Prompt.lecture_id.is_not(None).desc(),  # type: ignore
                    Prompt.id,  # type: ignore
                )
            )
            self.prompts = {p.id: p for p in prompts}
        self.unsaved_changes = False