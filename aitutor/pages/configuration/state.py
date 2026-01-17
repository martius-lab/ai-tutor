"""The state for the configuration page."""

import reflex as rx

from aitutor.auth.protection import state_require_role_at_least
from aitutor.auth.state import SessionState
from aitutor.language_state import BackendTranslations as BT
from aitutor.models import Config, UserRole

empty_config: Config = Config(
    id=None,
    check_conversation_prompt="failed to load!",
    response_ai_model="failed to load!",
    check_ai_model="failed to load!",
    how_to_use_text="failed to load!",
    general_information_text="failed to load!",
    lecture_information_text="failed to load!",
    course_name="failed to load!",
    impressum_text="failed to load!",
    registration_code="failed to load!",
)


class ManageConfigState(SessionState):
    """The State for the configuration page."""

    unsaved_changes: bool = False
    current_config: Config = empty_config

    @rx.event
    def set_unsaved_changes(self, unsaved: bool):
        """Sets the unsaved changes flag."""
        self.unsaved_changes = unsaved

    @rx.event
    def set_config_value(self, name: str, value: str):
        """Sets a configuration value in the current config."""
        setattr(self.current_config, name, value)
        self.unsaved_changes = True

    @rx.event
    @state_require_role_at_least(UserRole.TUTOR)
    def on_load(self):
        """Initialization for the page."""
        with rx.session() as session:
            _config = session.get(Config, 1)
            if _config is None:
                raise ValueError("Configuration not found in the database.")
            self.current_config = _config
        self.global_load()
        self.unsaved_changes = False

    def on_logout(self):
        """Clears the state when the user logs out."""
        self.unsaved_changes = False
        self.current_config = empty_config

    @rx.event
    def save_config_to_db(self):
        """Saves the current configuration to the database."""
        with rx.session() as session:
            db_config = session.get(Config, 1)
            if db_config:
                db_config.check_conversation_prompt = (
                    self.current_config.check_conversation_prompt
                )
                db_config.response_ai_model = self.current_config.response_ai_model
                db_config.check_ai_model = self.current_config.check_ai_model
                db_config.how_to_use_text = self.current_config.how_to_use_text
                db_config.general_information_text = (
                    self.current_config.general_information_text
                )
                db_config.lecture_information_text = (
                    self.current_config.lecture_information_text
                )
                db_config.course_name = self.current_config.course_name
                db_config.impressum_text = self.current_config.impressum_text
                db_config.registration_code = self.current_config.registration_code
                session.add(db_config)
                session.commit()

        self.unsaved_changes = False

        yield rx.toast.success(
            description=BT.config_saved(self.language),
            duration=5000,
            position="bottom-center",
            invert=True,
        )
