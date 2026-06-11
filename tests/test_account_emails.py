from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

import pytest
from reflex_local_auth.auth_session import LocalAuthSession
from reflex_local_auth.user import LocalUser
from sqlmodel import Session, SQLModel, create_engine, select

from aitutor.account_emails import (
    PASSWORD_RESET,
    AccountEmailToken,
    build_password_reset_link,
    create_account_token,
    get_valid_token,
    hash_token,
    reset_password,
    send_password_reset,
    send_signup_welcome,
)
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


def require_user_id(user: LocalUser) -> int:
    assert user.id is not None
    return user.id


@pytest.mark.parametrize(
    ("language", "expected_message"),
    [
        (Language.EN, "If an account exists"),
        (Language.DE, "Falls ein Konto"),
    ],
)
def test_account_email_backend_translations(language, expected_message):
    assert expected_message in BT.password_reset_requested_generic(language)


def test_password_reset_link_uses_public_base_url(monkeypatch):
    monkeypatch.setenv("AITUTOR_PUBLIC_URL", "https://ai-tutor.example/")

    assert build_password_reset_link("token-123") == (
        "https://ai-tutor.example/reset_password/token-123"
    )


def test_account_token_stores_hash_only():
    with make_session() as session:
        user = create_user(session)
        user_id = require_user_id(user)

        token = create_account_token(
            session,
            user_id=user_id,
            purpose=PASSWORD_RESET,
            ttl_hours=2,
        )
        session.commit()

        token_row = session.exec(select(AccountEmailToken)).one()
        assert token_row.token_hash == hash_token(token)
        assert token_row.token_hash != token
        assert get_valid_token(session, token=token, purpose=PASSWORD_RESET) is not None


def test_expired_or_used_token_is_not_valid():
    with make_session() as session:
        user = create_user(session)
        user_id = require_user_id(user)
        token = "raw-token"
        now = datetime.now(timezone.utc)
        session.add(
            AccountEmailToken(
                user_id=user_id,
                purpose=PASSWORD_RESET,
                token_hash=hash_token(token),
                created_at=now - timedelta(hours=3),
                expires_at=now - timedelta(hours=1),
            )
        )
        session.commit()

        assert get_valid_token(session, token=token, purpose=PASSWORD_RESET) is None

        token_row = session.exec(select(AccountEmailToken)).one()
        token_row.expires_at = now + timedelta(hours=1)
        token_row.used_at = now
        session.commit()

        assert get_valid_token(session, token=token, purpose=PASSWORD_RESET) is None


def test_reset_password_updates_hash_and_clears_sessions():
    with make_session() as session:
        user = create_user(session)
        user_id = require_user_id(user)
        token = create_account_token(
            session,
            user_id=user_id,
            purpose=PASSWORD_RESET,
            ttl_hours=2,
        )
        session.add(
            LocalAuthSession(
                user_id=user_id,
                session_id="existing-session",
                expiration=datetime.now(timezone.utc) + timedelta(days=1),
            )
        )
        session.commit()

        assert reset_password(session, token=token, new_password="new-password")
        session.commit()

        updated_user = session.get(LocalUser, user_id)
        assert updated_user is not None
        assert updated_user.verify("new-password")
        assert session.exec(select(LocalAuthSession)).all() == []
        assert get_valid_token(session, token=token, purpose=PASSWORD_RESET) is None


def test_send_password_reset_sends_email_without_account_enumeration(monkeypatch):
    sent_messages: list[EmailMessage] = []

    def fake_send_text_email(**kwargs):
        message = EmailMessage()
        message["To"] = kwargs["to_email"]
        message["Subject"] = kwargs["subject"]
        message.set_content(kwargs["body"])
        sent_messages.append(message)

    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_FROM_EMAIL", "noreply@example.com")
    monkeypatch.setenv("AITUTOR_PUBLIC_URL", "https://ai-tutor.example")
    monkeypatch.setattr("aitutor.account_emails.send_text_email", fake_send_text_email)

    with make_session() as session:
        create_user(session)

        send_password_reset(session, identifier="student@example.com")
        send_password_reset(session, identifier="missing@example.com")
        session.commit()

        assert len(sent_messages) == 1
        assert sent_messages[0]["To"] == "student@example.com"
        assert sent_messages[0]["Subject"] == "Reset your AI Tutor password"
        assert (
            "https://ai-tutor.example/reset_password/" in sent_messages[0].get_content()
        )


def test_send_password_reset_uses_user_language(monkeypatch):
    sent_messages: list[EmailMessage] = []

    def fake_send_text_email(**kwargs):
        message = EmailMessage()
        message["To"] = kwargs["to_email"]
        message["Subject"] = kwargs["subject"]
        message.set_content(kwargs["body"])
        sent_messages.append(message)

    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_FROM_EMAIL", "noreply@example.com")
    monkeypatch.setenv("AITUTOR_PUBLIC_URL", "https://ai-tutor.example")
    monkeypatch.setattr("aitutor.account_emails.send_text_email", fake_send_text_email)

    with make_session() as session:
        create_user(session, language=Language.DE)

        send_password_reset(session, identifier="student@example.com")
        session.commit()

    assert sent_messages[0]["Subject"] == "AI Tutor Passwort zurücksetzen"
    body = sent_messages[0].get_content()
    assert "Hallo student" in body
    assert "Dieser Link läuft in 2 Stunden ab." in body


def test_send_signup_welcome_sends_email(monkeypatch):
    sent_messages: list[EmailMessage] = []

    def fake_send_text_email(**kwargs):
        message = EmailMessage()
        message["To"] = kwargs["to_email"]
        message["Subject"] = kwargs["subject"]
        message.set_content(kwargs["body"])
        sent_messages.append(message)

    monkeypatch.setenv("AITUTOR_PUBLIC_URL", "https://ai-tutor.example")
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

    monkeypatch.setenv("AITUTOR_PUBLIC_URL", "https://ai-tutor.example")
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
