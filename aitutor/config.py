"""Configuration management of the application."""

import variconf
import reflex as rx
import sqlmodel
from dataclasses import dataclass

from aitutor.models import Config


DEFAULT_CONFIG_FILE_PATH = "./default_config.toml"
CONFIG_FILE_PATH = "./config.toml"


@dataclass
class ConfigDefaultUser:
    """Default users for testing."""

    role: str
    name: str
    password: str
    email: str


@dataclass
class ConfigExercisePrompt:
    """An excercise system prompt template."""

    name: str
    prompt: str


@dataclass
class AiTutorConfig:
    """Configuration class for AiTutor."""

    check_conversation_prompt: str
    response_ai_model: str
    check_ai_model: str
    how_to_use_text: str
    general_information_text: str
    lecture_information_text: str
    course_name: str
    impressum_text: str
    registration_code: str
    default_users: list[ConfigDefaultUser]
    exercise_prompts: list[ConfigExercisePrompt]


_config_from_file = None


def load_config_file():
    """Load configuration from file."""
    global _config_from_file
    wconf = variconf.WConf(AiTutorConfig)
    try:
        wconf.load_file(CONFIG_FILE_PATH)
    except FileNotFoundError:
        print(
            f"Config file {CONFIG_FILE_PATH} not found. Loading default config instead."
        )
        wconf.load_file(DEFAULT_CONFIG_FILE_PATH)

    _config_from_file = wconf.get()


def get_config_file() -> AiTutorConfig:
    """Get the content of the configuration file."""
    if _config_from_file is None:
        load_config_file()
    # Type of _config_from_file is actually some OmegaConf object, but it should have
    # the same fields as AiTutorConfig, so list that as return type for better
    # auto-completion.
    return _config_from_file  # type: ignore[return-value]


def get_config() -> AiTutorConfig:
    """Get the configuration from the database."""
    with rx.session() as session:
        _config = session.exec(
            sqlmodel.select(Config).where(Config.id == 1)
        ).one_or_none()
        if _config is None:
            raise ValueError("Configuration not found in the database.")
        return AiTutorConfig(
            check_conversation_prompt=_config.check_conversation_prompt,
            response_ai_model=_config.response_ai_model,
            check_ai_model=_config.check_ai_model,
            how_to_use_text=_config.how_to_use_text,
            general_information_text=_config.general_information_text,
            lecture_information_text=_config.lecture_information_text,
            course_name=_config.course_name,
            impressum_text=_config.impressum_text,
            registration_code=_config.registration_code,
            default_users=get_config_file().default_users,
            exercise_prompts=get_config_file().exercise_prompts,
        )


def get_config_db_model() -> Config:
    """Get the configuration as a database model instance."""
    with rx.session() as session:
        _config = session.exec(
            sqlmodel.select(Config).where(Config.id == 1)
        ).one_or_none()
        if _config is None:
            raise ValueError("Configuration not found in the database.")
        return _config
