"""Account welcome email helpers."""

import urllib.parse

from aitutor import routes
from aitutor.env_settings import get_env_settings
from aitutor.global_vars import VERIFICATION_TOKEN_VALIDITY
from aitutor.mail import send_text_email
from aitutor.models import Language


def public_base_url() -> str:
    """Public base URL used for links in account emails."""
    return f"https://{get_env_settings().DOMAIN}".rstrip("/")


def email_verification_url(token: str, language: Language) -> str:
    """
    Build the link a user has to open to confirm their email address.

    The link carries the language of the mail, so that the page it leads to is shown in
    the same language, even in a browser in which the user is not logged in.
    """
    query = urllib.parse.urlencode({"token": token, "lang": language.value})
    return f"{public_base_url()}{routes.VERIFY_EMAIL}?{query}"


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
            verification_url=email_verification_url(verification_token, language),
            validity_hours=validity_hours,
        ),
    )


def send_email_verification_email(
    *, to_email: str, username: str, language: Language, verification_token: str
) -> None:
    """
    Send a mail containing (only) the link to confirm an email address.

    Unlike :func:`send_signup_welcome_email` this does not welcome the user to a
    freshly created account.  It is used whenever a verification link is sent again
    later on, e.g. because the first one expired.
    """
    from aitutor.language_state import BackendTranslations as BT

    validity_hours = round(VERIFICATION_TOKEN_VALIDITY.total_seconds() / 3600)

    send_text_email(
        to_email=to_email,
        subject=BT.email_verification_subject(language),
        body=BT.email_verification_body(
            language,
            username=username,
            verification_url=email_verification_url(verification_token, language),
            validity_hours=validity_hours,
        ),
    )
