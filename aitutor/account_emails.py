"""Account welcome email helpers."""

from typing import cast

from decouple import config
from reflex_local_auth.user import LocalUser

from aitutor.mail import send_text_email
from aitutor.models import UserInfo


def public_base_url() -> str:
    """Public base URL used for links in account emails."""
    return cast(
        str, config("AITUTOR_PUBLIC_URL", default="http://localhost:3000", cast=str)
    ).rstrip("/")


def send_signup_welcome(*, local_user: LocalUser, user_info: UserInfo) -> None:
    """Send a welcome email for a newly registered account."""
    from aitutor.language_state import BackendTranslations as BT

    if local_user.id is None:
        raise ValueError("Cannot send welcome email before user is persisted.")
    login_url = f"{public_base_url()}/login"
    send_text_email(
        to_email=user_info.email,
        subject=BT.signup_welcome_subject(user_info.language),
        body=BT.signup_welcome_body(
            user_info.language,
            username=local_user.username,
            login_url=login_url,
        ),
    )
