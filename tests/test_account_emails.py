from email.message import EmailMessage

import pytest
from reflex_local_auth.user import LocalUser
from sqlmodel import Session, SQLModel, create_engine, select

from aitutor.account_emails import send_signup_welcome
from aitutor.language_state import BackendTranslations as BT
from aitutor.models import Language, UserInfo, UserRole


def make_session():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def create_user(session: Session, *, language: Language = Language.EN) -> LocalUser:
    user = LocalUser(
        username="student",
        password_hash=LocalUser.hash_password("old-password"),
        enabled=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    assert user.id is not None
    session.add(
        UserInfo(
            user_id=user.id,
            email="student@example.com",
            role=UserRole.STUDENT,
            language=language,
        )
    )
    session.commit()
    return user


@pytest.mark.parametrize(
    ("language", "expected_message"),
    [
        (Language.EN, "Welcome to AI Tutor"),
        (Language.DE, "Willkommen bei AI Tutor"),
    ],
)
def test_account_email_backend_translations(language, expected_message):
    assert expected_message in BT.signup_welcome_subject(language)


def test_send_signup_welcome_sends_email(monkeypatch):
    sent_messages: list[EmailMessage] = []

    def fake_send_text_email(**kwargs):
        message = EmailMessage()
        message["To"] = kwargs["to_email"]
        message["Subject"] = kwargs["subject"]
        message.set_content(kwargs["body"])
        sent_messages.append(message)

    monkeypatch.setenv("DOMAIN", "ai-tutor.example")
    monkeypatch.setattr("aitutor.account_emails.send_text_email", fake_send_text_email)

    with make_session() as session:
        user = create_user(session)
        user_info = session.exec(select(UserInfo)).one()

        send_signup_welcome(local_user=user, user_info=user_info)

    assert len(sent_messages) == 1
    assert sent_messages[0]["To"] == "student@example.com"
    assert sent_messages[0]["Subject"] == "Welcome to AI Tutor"
    assert "Username: student" in sent_messages[0].get_content()
    assert "https://ai-tutor.example/login" in sent_messages[0].get_content()


def test_send_signup_welcome_uses_user_language(monkeypatch):
    sent_messages: list[EmailMessage] = []

    def fake_send_text_email(**kwargs):
        message = EmailMessage()
        message["To"] = kwargs["to_email"]
        message["Subject"] = kwargs["subject"]
        message.set_content(kwargs["body"])
        sent_messages.append(message)

    monkeypatch.setenv("DOMAIN", "ai-tutor.example")
    monkeypatch.setattr("aitutor.account_emails.send_text_email", fake_send_text_email)

    with make_session() as session:
        user = create_user(session, language=Language.DE)
        user_info = session.exec(select(UserInfo)).one()

        send_signup_welcome(local_user=user, user_info=user_info)

    assert sent_messages[0]["Subject"] == "Willkommen bei AI Tutor"
    body = sent_messages[0].get_content()
    assert "Hallo student" in body
    assert "Benutzername: student" in body
    assert "https://ai-tutor.example/login" in body
