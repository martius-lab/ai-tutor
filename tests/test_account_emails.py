from email.message import EmailMessage

import pytest

from aitutor.account_emails import send_signup_welcome_email
from aitutor.app_settings import get_settings
from aitutor.language_state import BackendTranslations as BT
from aitutor.models import Language


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.parametrize(
    ("language", "expected_message"),
    [
        (Language.EN, "Welcome to AI Tutor"),
        (Language.DE, "Willkommen bei AI Tutor"),
    ],
)
def test_account_email_backend_translations(language, expected_message):
    assert expected_message in BT.signup_welcome_subject(language)


def test_send_signup_welcome_email_sends_email(monkeypatch):
    sent_messages: list[EmailMessage] = []

    def fake_send_text_email(**kwargs):
        message = EmailMessage()
        message["To"] = kwargs["to_email"]
        message["Subject"] = kwargs["subject"]
        message.set_content(kwargs["body"])
        sent_messages.append(message)

    monkeypatch.setenv("DOMAIN", "ai-tutor.example")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("aitutor.account_emails.send_text_email", fake_send_text_email)

    send_signup_welcome_email(
        to_email="student@example.com",
        username="student",
        language=Language.EN,
    )

    assert len(sent_messages) == 1
    assert sent_messages[0]["To"] == "student@example.com"
    assert sent_messages[0]["Subject"] == "Welcome to AI Tutor"
    assert "Username: student" in sent_messages[0].get_content()
    assert "https://ai-tutor.example/login" in sent_messages[0].get_content()


def test_send_signup_welcome_email_uses_user_language(monkeypatch):
    sent_messages: list[EmailMessage] = []

    def fake_send_text_email(**kwargs):
        message = EmailMessage()
        message["To"] = kwargs["to_email"]
        message["Subject"] = kwargs["subject"]
        message.set_content(kwargs["body"])
        sent_messages.append(message)

    monkeypatch.setenv("DOMAIN", "ai-tutor.example")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("aitutor.account_emails.send_text_email", fake_send_text_email)

    send_signup_welcome_email(
        to_email="student@example.com",
        username="student",
        language=Language.DE,
    )

    assert sent_messages[0]["Subject"] == "Willkommen bei AI Tutor"
    body = sent_messages[0].get_content()
    assert "Hallo student" in body
    assert "Benutzername: student" in body
    assert "https://ai-tutor.example/login" in body
