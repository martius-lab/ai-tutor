"""The state for the configuration page."""

import secrets
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import reflex as rx
from sqlmodel import select

import aitutor.global_vars as GV
from aitutor.auth.protection import state_require_role_or_permission
from aitutor.auth.state import SessionState
from aitutor.global_vars import TIME_ZONE
from aitutor.language_state import BackendTranslations as BT
from aitutor.models import (
    BannerMessageType,
    Config,
    LecturerRegistrationToken,
    UserRole,
)
from aitutor.states.banner_state import (
    INITIAL_BANNER_IS_OPEN,
    INITIAL_BANNER_MESSAGE,
    INITIAL_BANNER_MESSAGE_TYPE,
    BannerState,
)
from aitutor.states.config_state import DisplayConfigState

CONFIG_FIELD_MAX_LENGTHS: dict[str, int] = {
    "registration_code": GV.REGISTRATION_CODE_MAX_LEN,
    "response_ai_model": 100,
    "check_ai_model": 100,
    "how_to_use_text": 10_000,
    "general_information_text": 10_000,
    "impressum_text": 10_000,
}

empty_config: Config = Config(
    id=None,
    response_ai_model="failed to load!",
    check_ai_model="failed to load!",
    how_to_use_text="failed to load!",
    general_information_text="failed to load!",
    impressum_text="failed to load!",
    registration_code="failed to load!",
    exercise_token_limit=0,
    banner_message=INITIAL_BANNER_MESSAGE,
    banner_message_type=INITIAL_BANNER_MESSAGE_TYPE,
    banner_is_open=INITIAL_BANNER_IS_OPEN,
)


class ManageConfigState(SessionState):
    """The State for the configuration page."""

    unsaved_changes: bool = False
    current_config: Config = empty_config

    @rx.var
    def exercise_token_limit_str(self) -> str:
        """Returns the exercise token limit as a string for the input field."""
        return str(self.current_config.exercise_token_limit)

    @rx.event
    def set_unsaved_changes(self, unsaved: bool):
        """Sets the unsaved changes flag."""
        self.unsaved_changes = unsaved

    @rx.event
    def set_config_value(self, name: str, value: str):
        """Sets a configuration value in the current config."""
        # set max length for input fields coming from UI
        if name in CONFIG_FIELD_MAX_LENGTHS:
            value = value[: CONFIG_FIELD_MAX_LENGTHS[name]]
        setattr(self.current_config, name, value)
        self.unsaved_changes = True

    @rx.event
    def set_banner_is_open(self, value: bool):
        """Sets whether the banner is open in current config."""
        self.current_config.banner_is_open = value
        self.unsaved_changes = True

    @rx.event
    def set_banner_message_type(self, value: str):
        """Sets the banner message type in current config."""
        self.current_config.banner_message_type = BannerMessageType(value)
        self.unsaved_changes = True

    @rx.event
    def set_exercise_token_limit(self, value: str):
        """Sets exercise_token_limit while allowing transient invalid input states."""
        try:
            self.current_config.exercise_token_limit = max(1, int(value))
        except ValueError:
            pass
        self.unsaved_changes = True

    @rx.var
    def is_banner_message_invalid(self) -> bool:
        """Returns True if banner is open but message is empty."""
        return (
            self.current_config.banner_is_open
            and not self.current_config.banner_message.strip()
        )

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.TUTOR)
    def on_load(self):
        """Initialization for the page."""
        with rx.session() as session:
            _config = session.get(Config, 1)
            if _config is None:
                raise ValueError("Configuration not found in the database.")
            self.current_config = _config
        self.global_load()
        self.unsaved_changes = False

    @rx.event
    def save_config_to_db(self):
        """Saves the current configuration to the database."""
        if self.is_banner_message_invalid:
            yield rx.toast.error(
                description=BT.banner_message_empty(self.language),
                duration=5000,
                position="bottom-center",
                invert=True,
            )
            return
        with rx.session() as session:
            db_config = session.get(Config, 1)
            if db_config:
                db_config.response_ai_model = self.current_config.response_ai_model
                db_config.check_ai_model = self.current_config.check_ai_model
                db_config.how_to_use_text = self.current_config.how_to_use_text
                db_config.general_information_text = (
                    self.current_config.general_information_text
                )
                db_config.impressum_text = self.current_config.impressum_text
                db_config.registration_code = self.current_config.registration_code
                db_config.exercise_token_limit = (
                    self.current_config.exercise_token_limit
                )
                db_config.banner_message = self.current_config.banner_message
                db_config.banner_message_type = self.current_config.banner_message_type
                db_config.banner_is_open = self.current_config.banner_is_open
                session.add(db_config)
                session.commit()

        self.unsaved_changes = False

        yield DisplayConfigState.refresh_config_strings
        yield BannerState.refresh_banner
        yield rx.toast.success(
            description=BT.config_saved(self.language),
            duration=5000,
            position="bottom-center",
            invert=True,
        )


class LecturerRegistrationTokenState(SessionState):
    """The State for the lecturer registration token management."""

    tokens: list[LecturerRegistrationToken] = []
    link_base: str
    default_expires_at: str

    add_dialog_is_open: bool = False

    @rx.event
    def set_add_dialog_is_open(self, is_open: bool):
        """Sets the state of the add dialog."""
        self.add_dialog_is_open = is_open

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.ADMIN)
    def on_load(self):
        """Initialize the state"""
        self.global_load()

        self.link_base = f"{self.router.url.origin}/register?lrt="
        self.default_expires_at = (
            datetime.now(ZoneInfo(TIME_ZONE)) + timedelta(days=14)
        ).strftime("%Y-%m-%d")

        with rx.session() as session:
            stmt = select(LecturerRegistrationToken).order_by(
                LecturerRegistrationToken.created_at  # type: ignore
            )
            self.tokens = list(session.exec(stmt).all())

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.ADMIN)
    def generate_new_token(self, form_data: dict):
        """Generates a new lecturer registration token."""
        assert self.authenticated_user.id is not None

        now = datetime.now(ZoneInfo(TIME_ZONE))
        expires_at = datetime.strptime(form_data["expires_at"], "%Y-%m-%d").replace(
            tzinfo=ZoneInfo(TIME_ZONE), hour=23, minute=59, second=59
        )

        # For security reasons, limit the max. lifetime of the tokens.
        max_duration_days = 60
        if expires_at - now > timedelta(days=max_duration_days):
            return rx.toast.error(
                description=BT.lecturer_registration_token_expiration_too_long(
                    self.language, max_duration_days
                ),
                duration=5000,
                position="bottom-center",
            )

        with rx.session() as session:
            new_token = LecturerRegistrationToken(
                token=secrets.token_urlsafe(32),
                created_by=self.authenticated_user.id,
                created_at=now,
                expires_at=expires_at,
            )
            session.add(new_token)
            session.commit()
            session.refresh(new_token)
            self.tokens.append(new_token)

        self.add_dialog_is_open = False

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.ADMIN)
    def delete_token(self, token_id: int):
        """Deletes a lecturer registration token."""
        with rx.session() as session:
            token = session.get(LecturerRegistrationToken, token_id)
            if token:
                session.delete(token)
                session.commit()
                self.tokens = [t for t in self.tokens if t.id != token_id]
