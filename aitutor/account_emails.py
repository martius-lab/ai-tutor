"""Account welcome email helpers."""

from aitutor import routes
from aitutor.env_settings import get_env_settings
from aitutor.global_vars import VERIFICATION_TOKEN_VALIDITY
from aitutor.mail import send_text_email
from aitutor.models import Language


def public_base_url() -> str:
    """Public base URL used for links in account emails."""
    return f"https://{get_env_settings().DOMAIN}".rstrip("/")


def email_verification_url(token: str) -> str:
    """Build the link a user has to open to confirm their email address."""
    return f"{public_base_url()}{routes.VERIFY_EMAIL}/{token}"


def send_signup_welcome_email(
    *, to_email: str, username: str, language: Language, verification_token: str
) -> None:
    """Send a welcome email containing the link to verify the email address."""
    from aitutor.language_state import BackendTranslations as BT

    validity_hours = round(VERIFICATION_TOKEN_VALIDITY.total_seconds() / 3600)

    send_text_email(
        to_email=to_email,
        subject=BT.signup_welcome_subject(language),
        body=BT.signup_welcome_body(
            language,
            username=username,
            verification_url=email_verification_url(verification_token),
            validity_hours=validity_hours,
        ),
    )
