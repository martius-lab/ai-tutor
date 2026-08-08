"""SMTP email helpers for account-related messages."""

from email.message import EmailMessage
from smtplib import SMTP, SMTP_SSL, SMTPException
from typing import Any, Callable

from aitutor.env_settings import SmtpSettings, get_env_settings


class EmailDeliveryError(RuntimeError):
    """Raised when an email could not be delivered through SMTP."""


def build_text_email(
    *,
    from_email: str,
    to_email: str,
    subject: str,
    body: str,
) -> EmailMessage:
    """Build a plain text email message."""
    message = EmailMessage()
    message["From"] = from_email
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)
    return message


def send_text_email(
    *,
    to_email: str,
    subject: str,
    body: str,
    settings: SmtpSettings | None = None,
) -> None:
    """Build and send a plain text email message."""
    settings = settings or get_env_settings().SMTP

    # settings may be None, which means no SMTP is configured.  In this case, simply
    # print the email to stdout for debugging.

    from_email = settings.FROM_EMAIL if settings else "Testing <test@localhost>"
    mail = build_text_email(
        from_email=from_email,
        to_email=to_email,
        subject=subject,
        body=body,
    )
    if settings:
        send_email(mail, settings=settings)
    else:
        print_mail(mail)


def print_mail(
    message: EmailMessage,
) -> None:
    """Print the email message to stdout for debugging."""
    print("=== Email Message ===")
    print(message)
    print("=====================")


def send_email(
    message: EmailMessage,
    *,
    settings: SmtpSettings,
    smtp_client_cls: Callable[..., Any] | None = None,
) -> None:
    """Send an email message through the configured SMTP server."""
    client_cls = smtp_client_cls or (SMTP_SSL if settings.USE_SSL else SMTP)

    try:
        with client_cls(
            settings.HOST,
            settings.PORT,
            timeout=settings.TIMEOUT,
        ) as smtp:
            if settings.USE_TLS:
                smtp.starttls()
                smtp.ehlo()
            if settings.USERNAME and settings.PASSWORD:
                smtp.login(settings.USERNAME, settings.PASSWORD)
            smtp.send_message(message)
    except (OSError, SMTPException) as exc:
        raise EmailDeliveryError("Failed to send email via SMTP.") from exc
