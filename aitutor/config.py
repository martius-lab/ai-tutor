"""Configuration management of the application."""

from dataclasses import dataclass

import variconf


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
    default_users: list[ConfigDefaultUser]
    exercise_prompts: list[ConfigExercisePrompt]


_config = None


def load_config():
    """Load configuration from file."""
    global _config
    wconf = variconf.WConf(AiTutorConfig)
    try:
        wconf.load_file(CONFIG_FILE_PATH)
    except FileNotFoundError:
        print(
            f"Config file {CONFIG_FILE_PATH} not found. Loading default config instead."
        )
        wconf.load_file(DEFAULT_CONFIG_FILE_PATH)

    _config = wconf.get()


def get_config() -> AiTutorConfig:
    """Get the configuration object."""
    if _config is None:
        load_config()
    # Type of _config is actually some OmegaConf object, but it should have the same
    # fields as AiTutorConfig, so list that as return type for better auto-completion.
    return _config  # type: ignore[return-value]


_privacy_notice = None


def load_privacy_notice():
    """Load the privacy notice text from datenschutz.md."""
    global _privacy_notice
    try:
        with open("datenschutz.md", "r", encoding="utf-8") as f:
            _privacy_notice = f.read()
    except FileNotFoundError:
        print("Warning: datenschutz.md not found. Using empty privacy notice.")
        _privacy_notice = ""


def get_privacy_notice() -> str:
    """Get the privacy notice text from datenschutz.md."""
    if _privacy_notice is None:
        load_privacy_notice()
    assert _privacy_notice is not None
    return _privacy_notice
