"""Account welcome email helpers."""

from aitutor.app_settings import get_settings
from aitutor.mail import send_text_email
from aitutor.models import Language


def public_base_url() -> str:
    """Public base URL used for links in account emails."""
    return f"https://{get_settings().domain}".rstrip("/")


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
