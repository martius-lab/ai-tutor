"""Configuration management of the application."""

from dataclasses import dataclass

import reflex as rx
import variconf
from sqlmodel import select

from aitutor.models import Config, Prompt

# Config File --------------------------------------------------------------------------

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
class ConfigFile:
    """Configuration class for the AiTutor config file."""

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


def load_config_from_file():
    """Load configuration from file."""
    global _config_from_file
    wconf = variconf.WConf(ConfigFile)
    try:
        wconf.load_file(CONFIG_FILE_PATH)
    except FileNotFoundError:
        print(
            f"Config file {CONFIG_FILE_PATH} not found. Loading default config instead."
        )
        wconf.load_file(DEFAULT_CONFIG_FILE_PATH)

    _config_from_file = wconf.get()


def get_config_from_file() -> ConfigFile:
    """Get the content of the configuration file."""
    if _config_from_file is None:
        load_config_from_file()
    # Type of _config_from_file is actually some OmegaConf object, but it should have
    # the same fields as ConfigFile, so list that as return type for better
    # auto-completion.
    return _config_from_file  # type: ignore[return-value]


def add_configprompts_to_db():
    """Add prompts from the config file to the database."""
    with rx.session() as session:
        existing_prompts = session.exec(select(Prompt))
        existing_prompt_names = {prompt.name for prompt in existing_prompts}

        config_file = get_config_from_file()
        for prompt_cfg in config_file.exercise_prompts:
            if prompt_cfg.name not in existing_prompt_names:
                prompt = Prompt(
                    name=prompt_cfg.name,
                    prompt_template=prompt_cfg.prompt,
                )
                session.add(prompt)
                print(f"Added prompt '{prompt_cfg.name}' to the database.")
                session.commit()


# Config DB ----------------------------------------------------------------------------


def initialize_config_db():
    """ensure there is a config row in the database."""
    with rx.session() as session:
        config_row = session.get(Config, 1)
        if not config_row:
            config_file = get_config_from_file()
            config = Config(
                id=1,
                check_conversation_prompt=config_file.check_conversation_prompt,
                response_ai_model=config_file.response_ai_model,
                check_ai_model=config_file.check_ai_model,
                how_to_use_text=config_file.how_to_use_text,
                general_information_text=config_file.general_information_text,
                lecture_information_text=config_file.lecture_information_text,
                course_name=config_file.course_name,
                impressum_text=config_file.impressum_text,
                registration_code=config_file.registration_code,
            )
            session.add(config)
            session.commit()
            print("Configuration row added to the database.")
        else:
            print("Configuration row exists in the database.")


def get_config() -> Config:
    """Get the configuration from the database."""
    with rx.session() as session:
        _config = session.get(Config, 1)
        if _config is None:
            raise ValueError("Configuration not found in the database.")
        return Config(
            check_conversation_prompt=_config.check_conversation_prompt,
            response_ai_model=_config.response_ai_model,
            check_ai_model=_config.check_ai_model,
            how_to_use_text=_config.how_to_use_text,
            general_information_text=_config.general_information_text,
            lecture_information_text=_config.lecture_information_text,
            course_name=_config.course_name,
            impressum_text=_config.impressum_text,
            registration_code=_config.registration_code,
        )
