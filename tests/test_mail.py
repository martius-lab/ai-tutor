from email.message import EmailMessage

import pytest

from aitutor.mail import (
    EmailConfigurationError,
    SmtpSettings,
    build_text_email,
    send_email,
)


class FakeSmtpClient:
    """SMTP client test double that records calls without sending email."""

    instances = []

    def __init__(self, host, port, timeout):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.started_tls = False
        self.login_args = None
        self.sent_messages = []
        FakeSmtpClient.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return None

    def starttls(self):
        self.started_tls = True

    def login(self, username, password):
        self.login_args = (username, password)

    def send_message(self, message):
        self.sent_messages.append(message)


def test_smtp_settings_from_env(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtpserv.uni-tuebingen.de")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_FROM_EMAIL", "AI Tutor <noreply@example.com>")
    monkeypatch.setenv("SMTP_USERNAME", "smtp-user")
    monkeypatch.setenv("SMTP_PASSWORD", "smtp-password")
    monkeypatch.setenv("SMTP_USE_TLS", "true")
    monkeypatch.setenv("SMTP_USE_SSL", "false")

    settings = SmtpSettings.from_env()

    assert settings.host == "smtpserv.uni-tuebingen.de"
    assert settings.port == 587
    assert settings.from_email == "AI Tutor <noreply@example.com>"
    assert settings.username == "smtp-user"
    assert settings.password == "smtp-password"
    assert settings.use_tls is True
    assert settings.use_ssl is False
    assert settings.uses_authentication is True


def test_smtp_settings_require_host(monkeypatch):
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.setenv("SMTP_FROM_EMAIL", "noreply@example.com")

    with pytest.raises(EmailConfigurationError, match="SMTP_HOST"):
        SmtpSettings.from_env()


def test_smtp_settings_reject_partial_credentials():
    settings = SmtpSettings(
        host="smtp.example.com",
        port=587,
        from_email="noreply@example.com",
        username="smtp-user",
    )

    with pytest.raises(EmailConfigurationError, match="SMTP_USERNAME"):
        settings.validate()


def test_build_text_email_uses_configured_sender():
    settings = SmtpSettings(
        host="smtp.example.com",
        port=587,
        from_email="AI Tutor <noreply@example.com>",
    )

    message = build_text_email(
        to_email="student@example.com",
        subject="Confirm your AI Tutor account",
        body="Welcome to AI Tutor.",
        settings=settings,
    )

    assert message["From"] == "AI Tutor <noreply@example.com>"
    assert message["To"] == "student@example.com"
    assert message["Subject"] == "Confirm your AI Tutor account"
    assert message.get_content() == "Welcome to AI Tutor.\n"


def test_send_email_uses_starttls_and_authentication():
    FakeSmtpClient.instances.clear()
    settings = SmtpSettings(
        host="smtp.example.com",
        port=587,
        from_email="noreply@example.com",
        username="smtp-user",
        password="smtp-password",
        use_tls=True,
    )
    message = EmailMessage()
    message["From"] = settings.from_email
    message["To"] = "student@example.com"
    message["Subject"] = "Test"
    message.set_content("Body")

    send_email(message, settings=settings, smtp_client_cls=FakeSmtpClient)

    client = FakeSmtpClient.instances[0]
    assert client.host == "smtp.example.com"
    assert client.port == 587
    assert client.timeout == 10
    assert client.started_tls is True
    assert client.login_args == ("smtp-user", "smtp-password")
    assert client.sent_messages == [message]
