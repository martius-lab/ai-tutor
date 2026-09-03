"""Configuration management of the application."""

import secrets

import reflex as rx

from aitutor.models import BannerMessageType, Config


def get_default_admin_user() -> dict:
    """Default admin user that is initially created."""
    return {
        "name": "admin",
        "password": secrets.token_urlsafe(16),
        "email": "admin@example.com",
    }


def get_default_config() -> Config:
    """Get the default configuration."""
    return Config(
        response_ai_model="gpt-4.1-mini",
        check_ai_model="gpt-4.1",
        how_to_use_text="""
I am your AI tutor and I want to help you understand the content of the lecture. Here's
how it works:

1. Explain to me the question I ask you at the beginning of the conversation.
2. When you think the question has been answered – and I also confirm that it has been
   answered – you can use the "Check Answer" button to verify the conversation. A
   separate AI will then check whether the task was solved correctly. If the check is
   successful, you can submit the chat history.

I’m looking forward to working with you!
""",
        general_information_text="""
- The AI tutor should only be used for working on the tasks.
- Tutors and lecturers can view chats that have been submitted.
""",
        impressum_text="",
        registration_code=secrets.token_urlsafe(16),
        exercise_token_limit=100_000,
        banner_message="",
        banner_message_type=BannerMessageType.INFO,
        banner_is_open=False,
    )


def get_default_prompts() -> list[dict]:
    """Get the default prompts."""
    return [
        {
            "name": "Helpful Learner",
            "prompt_template": """
You will act as a learning assistant.
Using the inverted teaching methods, a university student is given the task to explain
"{title}" with description "{description}"
This is the lesson context uploaded by the teacher as a basis for this exercise:
--------------------------
{lesson_context}
--------------------------
The user is a student who should explain the matter to you in a conversation.
You pretend to be a learner trying to understand {description}.
The student will complete the exercise in a conversation with you.
If the student answered the task "{description}" incorrectly, you can give them a hint
to help them find the solution but do NOT tell them the solution.
If the student explained the task "{description}" overall correctly, you will tell them
that they are correct and the task is finished. Keep you communication concise.
Do not engage in any other topics than the exercise at hand. If the student asks
anything unrelated, tell them that you are only here to help with the exercise.
""",
        },
    ]


def _parse_banner_message_type(val: str) -> BannerMessageType:
    return BannerMessageType(val)


def get_config() -> Config:
    """Get the configuration from the database."""
    with rx.session() as session:
        _config = session.get(Config, 1)
        if _config is None:
            raise ValueError("Configuration not found in the database.")
        return Config(
            response_ai_model=_config.response_ai_model,
            check_ai_model=_config.check_ai_model,
            how_to_use_text=_config.how_to_use_text,
            general_information_text=_config.general_information_text,
            impressum_text=_config.impressum_text,
            registration_code=_config.registration_code,
            exercise_token_limit=_config.exercise_token_limit,
            banner_message=_config.banner_message,
            banner_message_type=_parse_banner_message_type(_config.banner_message_type),
            banner_is_open=_config.banner_is_open,
        )
