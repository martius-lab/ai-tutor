"""Configuration management of the application."""

from dataclasses import dataclass

import variconf


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
class ConfigCheckConversationPrompt:
    """A "check conversation" system prompt."""

    prompt: str


@dataclass
class AiTutorConfig:
    """Configuration class for AiTutor."""

    default_users: list[ConfigDefaultUser]
    exercise_prompts: list[ConfigExercisePrompt]
    check_conversation_prompt: ConfigCheckConversationPrompt


_config = None


def load_config():
    """Load configuration from file."""
    global _config
    wconf = variconf.WConf(AiTutorConfig)
    wconf.load_file(CONFIG_FILE_PATH)
    _config = wconf.get()


def get_config() -> AiTutorConfig:
    """Get the configuration object."""
    if _config is None:
        load_config()
    # Type of _config is actually some OmegaConf object, but it should have the same
    # fields as AiTutorConfig, so list that as return type for better auto-completion.
    return _config  # type: ignore[return-value]
