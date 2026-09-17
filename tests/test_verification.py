from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from aitutor.global_vars import TIME_ZONE, VERIFICATION_TOKEN_VALIDITY
from aitutor.models import VerificationPurpose, VerificationToken
from aitutor.verification import issue_token


@pytest.fixture
def session():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_issue_token_stores_only_the_hash(session):
    token = issue_token(session, user_id=1, email="student@example.com")
    session.commit()

    entry = session.exec(select(VerificationToken)).one()
    assert token != ""
    assert entry.token_hash != token
    assert entry.token_hash == VerificationToken.hash_token(token)
    assert entry.email == "student@example.com"
    assert entry.purpose == VerificationPurpose.EMAIL
    assert entry.used_at is None


def test_issue_token_returns_a_new_token_every_time(session):
    first = issue_token(session, user_id=1, email="student@example.com")
    session.commit()
    second = issue_token(session, user_id=2, email="other@example.com")
    session.commit()

    assert first != second


def test_issue_token_sets_expiry(session):
    issue_token(session, user_id=1, email="student@example.com")
    session.commit()

    entry = session.exec(select(VerificationToken)).one()
    validity = entry.expires_at - entry.created_at
    assert abs(validity - VERIFICATION_TOKEN_VALIDITY) < timedelta(seconds=10)


def test_issue_token_replaces_an_existing_token(session):
    old_token = issue_token(session, user_id=1, email="student@example.com")
    session.commit()
    new_token = issue_token(session, user_id=1, email="new@example.com")
    session.commit()

    entries = session.exec(select(VerificationToken)).all()
    assert len(entries) == 1
    # the old token does not work anymore, the new one does
    assert entries[0].token_hash != VerificationToken.hash_token(old_token)
    assert entries[0].token_hash == VerificationToken.hash_token(new_token)
    # and it now verifies the new address
    assert entries[0].email == "new@example.com"


def test_issue_token_resets_used_at(session):
    issue_token(session, user_id=1, email="student@example.com")
    session.commit()
    entry = session.exec(select(VerificationToken)).one()
    entry.used_at = datetime.now(ZoneInfo(TIME_ZONE))
    session.commit()

    issue_token(session, user_id=1, email="student@example.com")
    session.commit()

    entry = session.exec(select(VerificationToken)).one()
    assert entry.used_at is None


def test_issue_token_keeps_purposes_apart(session):
    issue_token(
        session,
        user_id=1,
        email="student@example.com",
        purpose=VerificationPurpose.EMAIL,
    )
    issue_token(
        session,
        user_id=1,
        email="student@example.com",
        purpose=VerificationPurpose.PASSWORD_RESET,
    )
    session.commit()

    entries = session.exec(select(VerificationToken)).all()
    assert len(entries) == 2
    assert {entry.purpose for entry in entries} == set(VerificationPurpose)
