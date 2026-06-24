"""SMTP email helpers for account-related messages."""

from dataclasses import dataclass
from email.message import EmailMessage
from smtplib import SMTP, SMTP_SSL, SMTPException
from typing import Any, Callable

from aitutor.app_settings import get_settings


class EmailConfigurationError(RuntimeError):
    """Raised when email sending is requested without valid SMTP settings."""


class EmailDeliveryError(RuntimeError):
    """Raised when an email could not be delivered through SMTP."""


@dataclass(frozen=True)
class SmtpSettings:
    """Runtime SMTP settings loaded from the deployment environment."""

    host: str
    port: int
    from_email: str
    username: str = ""
    password: str = ""
    use_tls: bool = True
    use_ssl: bool = False
    timeout: int = 10

    @classmethod
    def from_env(cls) -> "SmtpSettings":
        """Load and validate SMTP settings from environment variables."""
        app_settings = get_settings()
        use_ssl = app_settings.smtp_use_ssl
        settings = cls(
            host=app_settings.smtp_host,
            port=app_settings.smtp_port or (465 if use_ssl else 587),
            from_email=app_settings.smtp_from_email,
            username=app_settings.smtp_username,
            password=app_settings.smtp_password,
            use_tls=(
                not use_ssl
                if app_settings.smtp_use_tls is None
                else app_settings.smtp_use_tls
            ),
            use_ssl=use_ssl,
            timeout=app_settings.smtp_timeout,
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        """Validate settings needed for SMTP delivery."""
        if not self.host:
            raise EmailConfigurationError("SMTP_HOST is required to send email.")
        if not self.from_email:
            raise EmailConfigurationError("SMTP_FROM_EMAIL is required to send email.")
        if self.port <= 0:
            raise EmailConfigurationError("SMTP_PORT must be greater than 0.")
        if self.timeout <= 0:
            raise EmailConfigurationError("SMTP_TIMEOUT must be greater than 0.")
        if self.use_tls and self.use_ssl:
            raise EmailConfigurationError(
                "SMTP_USE_TLS and SMTP_USE_SSL cannot both be enabled."
            )
        if bool(self.username) != bool(self.password):
            raise EmailConfigurationError(
                "SMTP_USERNAME and SMTP_PASSWORD must be configured together."
            )

    @property
    def uses_authentication(self) -> bool:
        """Whether SMTP username/password authentication is configured."""
        return bool(self.username and self.password)


def build_text_email(
    *,
    to_email: str,
    subject: str,
    body: str,
    settings: SmtpSettings | None = None,
) -> EmailMessage:
    """Build a plain text email message."""
    active_settings = settings or SmtpSettings.from_env()
    message = EmailMessage()
    message["From"] = active_settings.from_email
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
    active_settings = settings or SmtpSettings.from_env()
    send_email(
        build_text_email(
            to_email=to_email,
            subject=subject,
            body=body,
            settings=active_settings,
        ),
        settings=active_settings,
    )


def send_email(
    message: EmailMessage,
    *,
    settings: SmtpSettings | None = None,
    smtp_client_cls: Callable[..., Any] | None = None,
) -> None:
    """Send an email message through the configured SMTP server."""
    active_settings = settings or SmtpSettings.from_env()
    active_settings.validate()
    client_cls = smtp_client_cls or (SMTP_SSL if active_settings.use_ssl else SMTP)

    try:
        with client_cls(
            active_settings.host,
            active_settings.port,
            timeout=active_settings.timeout,
        ) as smtp:
            if active_settings.use_tls:
                smtp.starttls()
                smtp.ehlo()
            if active_settings.uses_authentication:
                smtp.login(active_settings.username, active_settings.password)
            smtp.send_message(message)
    except (OSError, SMTPException) as exc:
        raise EmailDeliveryError("Failed to send email via SMTP.") from exc
