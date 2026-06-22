"""Account welcome email helpers."""

from typing import cast

from decouple import config
from reflex_local_auth.user import LocalUser

from aitutor.mail import send_text_email
from aitutor.models import Language, UserInfo


def public_base_url() -> str:
    """Public base URL used for links in account emails."""
    domain = cast(str, config("DOMAIN", default="localhost", cast=str)).strip()
    return f"https://{domain}".rstrip("/")


def send_signup_welcome(*, local_user: LocalUser, user_info: UserInfo) -> None:
    """Send a welcome email for a newly registered account."""
    if local_user.id is None:
        raise ValueError("Cannot send welcome email before user is persisted.")
    send_signup_welcome_email(
        to_email=user_info.email,
        username=local_user.username,
        language=user_info.language,
    )


def send_signup_welcome_email(
    *, to_email: str, username: str, language: Language
) -> None:
    """Send a welcome email using plain account values."""
    from aitutor.language_state import BackendTranslations as BT

    send_text_email(
        to_email=to_email,
        subject=BT.signup_welcome_subject(language),
        body=BT.signup_welcome_body(
            language,
            username=username,
            login_url=f"{public_base_url()}/login",
        ),
    )
