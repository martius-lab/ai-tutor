from email.message import EmailMessage

import pytest

from aitutor.app_settings import SmtpSettings, get_settings
from aitutor.mail import (
    build_text_email,
    send_email,
)


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


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
        self.calls = []
        FakeSmtpClient.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return None

    def starttls(self):
        self.calls.append("starttls")
        self.started_tls = True

    def ehlo(self):
        self.calls.append("ehlo")

    def login(self, username, password):
        self.calls.append("login")
        self.login_args = (username, password)

    def send_message(self, message):
        self.calls.append("send_message")
        self.sent_messages.append(message)


def test_build_text_email_uses_configured_sender():
    message = build_text_email(
        from_email="AI Tutor <noreply@example.com>",
        to_email="student@example.com",
        subject="Confirm your AI Tutor account",
        body="Welcome to AI Tutor.",
    )

    assert message["From"] == "AI Tutor <noreply@example.com>"
    assert message["To"] == "student@example.com"
    assert message["Subject"] == "Confirm your AI Tutor account"
    assert message.get_content() == "Welcome to AI Tutor.\n"


def test_send_email_uses_starttls_and_authentication():
    FakeSmtpClient.instances.clear()
    settings = SmtpSettings(
        HOST="smtp.example.com",
        PORT=587,
        FROM_EMAIL="noreply@example.com",
        USERNAME="smtp-user",
        PASSWORD="smtp-password",
        USE_TLS=True,
    )
    message = EmailMessage()
    message["From"] = settings.FROM_EMAIL
    message["To"] = "student@example.com"
    message["Subject"] = "Test"
    message.set_content("Body")

    send_email(message, settings=settings, smtp_client_cls=FakeSmtpClient)

    client = FakeSmtpClient.instances[0]
    assert client.host == "smtp.example.com"
    assert client.port == 587
    assert client.timeout == 10
    assert client.started_tls is True
    assert client.calls == ["starttls", "ehlo", "login", "send_message"]
    assert client.login_args == ("smtp-user", "smtp-password")
    assert client.sent_messages == [message]
