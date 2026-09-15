from email.message import EmailMessage

import pytest

from aitutor.account_emails import send_signup_welcome_email
from aitutor.env_settings import get_env_settings
from aitutor.language_state import BackendTranslations as BT
from aitutor.models import Language


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_env_settings.cache_clear()
    yield
    get_env_settings.cache_clear()


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
        verification_token="tok3n",
    )

    assert len(sent_messages) == 1
    assert sent_messages[0]["To"] == "student@example.com"
    assert "Welcome to AI Tutor" in sent_messages[0]["Subject"]
    body = sent_messages[0].get_content()
    assert "Username: student" in body
    assert "https://ai-tutor.example/verify_email/tok3n" in body
    # the validity of the token is announced in the mail
    assert "48 hours" in body


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
        verification_token="tok3n",
    )

    assert "Willkommen bei AI Tutor" in sent_messages[0]["Subject"]
    body = sent_messages[0].get_content()
    assert "Hallo student" in body
    assert "Benutzername: student" in body
    assert "https://ai-tutor.example/verify_email/tok3n" in body
