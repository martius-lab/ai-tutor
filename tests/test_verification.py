from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from aitutor.global_vars import (
    TIME_ZONE,
    VERIFICATION_RESEND_COOLDOWN,
    VERIFICATION_TOKEN_VALIDITY,
)
from aitutor.models import (
    UserInfo,
    UserRole,
    VerificationPurpose,
    VerificationToken,
)
from aitutor.verification import (
    RedeemResult,
    issue_token,
    redeem_email_token,
    resend_cooldown_remaining,
)


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


def test_resend_cooldown_is_zero_without_a_token(session):
    assert resend_cooldown_remaining(session, user_id=1) == timedelta(0)


def test_resend_cooldown_starts_when_a_token_is_issued(session):
    issue_token(session, user_id=1, email="student@example.com")
    session.commit()

    remaining = resend_cooldown_remaining(session, user_id=1)
    assert remaining > timedelta(0)
    assert remaining <= VERIFICATION_RESEND_COOLDOWN


def test_resend_cooldown_is_over_after_the_cooldown_period(session):
    issue_token(session, user_id=1, email="student@example.com")
    session.commit()

    entry = session.exec(select(VerificationToken)).one()
    entry.last_sent_at = (
        datetime.now(ZoneInfo(TIME_ZONE))
        - VERIFICATION_RESEND_COOLDOWN
        - timedelta(seconds=1)
    )
    session.commit()

    assert resend_cooldown_remaining(session, user_id=1) == timedelta(0)


def test_resend_cooldown_is_per_user(session):
    issue_token(session, user_id=1, email="student@example.com")
    session.commit()

    assert resend_cooldown_remaining(session, user_id=2) == timedelta(0)


def test_resend_cooldown_is_per_purpose(session):
    issue_token(
        session,
        user_id=1,
        email="student@example.com",
        purpose=VerificationPurpose.PASSWORD_RESET,
    )
    session.commit()

    assert resend_cooldown_remaining(session, user_id=1) == timedelta(0)
    assert resend_cooldown_remaining(
        session, user_id=1, purpose=VerificationPurpose.PASSWORD_RESET
    ) > timedelta(0)


def make_user_info(session, *, user_id=1, email="old@example.com"):
    """Create the UserInfo row a token redemption operates on."""
    user_info = UserInfo(user_id=user_id, email=email, role=UserRole.STUDENT)
    session.add(user_info)
    session.commit()
    return user_info


def test_redeem_unknown_token(session):
    assert redeem_email_token(session, "no-such-token") == RedeemResult.UNKNOWN


def test_redeem_empty_token(session):
    assert redeem_email_token(session, "") == RedeemResult.UNKNOWN


def test_redeem_confirms_the_address(session):
    user_info = make_user_info(session)
    token = issue_token(session, user_id=1, email="old@example.com")
    session.commit()

    assert redeem_email_token(session, token) == RedeemResult.SUCCESS
    session.commit()

    assert user_info.verified is True
    assert session.exec(select(VerificationToken)).one().used_at is not None


def test_redeem_applies_a_pending_email_change(session):
    user_info = make_user_info(session, email="old@example.com")
    # the address the token confirms is not the one currently on the account
    token = issue_token(session, user_id=1, email="new@example.com")
    session.commit()

    assert redeem_email_token(session, token) == RedeemResult.SUCCESS
    session.commit()

    assert user_info.email == "new@example.com"
    assert user_info.verified is True


def test_redeem_is_idempotent_within_the_validity_window(session):
    # a mail gateway opening the link before the user must not break it for them
    user_info = make_user_info(session)
    token = issue_token(session, user_id=1, email="student@example.com")
    session.commit()

    assert redeem_email_token(session, token) == RedeemResult.SUCCESS
    session.commit()
    assert redeem_email_token(session, token) == RedeemResult.ALREADY_USED
    session.commit()

    assert user_info.verified is True


def test_redeem_expired_token(session):
    user_info = make_user_info(session)
    token = issue_token(session, user_id=1, email="student@example.com")
    session.commit()

    entry = session.exec(select(VerificationToken)).one()
    entry.expires_at = datetime.now(ZoneInfo(TIME_ZONE)) - timedelta(seconds=1)
    session.commit()

    assert redeem_email_token(session, token) == RedeemResult.EXPIRED
    session.commit()

    assert user_info.verified is False
    assert session.exec(select(VerificationToken)).one().used_at is None


def test_redeem_ignores_tokens_of_another_purpose(session):
    make_user_info(session)
    token = issue_token(
        session,
        user_id=1,
        email="student@example.com",
        purpose=VerificationPurpose.PASSWORD_RESET,
    )
    session.commit()

    assert redeem_email_token(session, token) == RedeemResult.UNKNOWN


def test_redeem_reports_an_error_for_an_account_without_user_info(session):
    # deliberately no UserInfo row, i.e. an inconsistent database
    token = issue_token(session, user_id=1, email="student@example.com")
    session.commit()

    assert redeem_email_token(session, token) == RedeemResult.ERROR
    session.commit()

    # the token is not burned by this, so it still works once the database is fixed
    assert session.exec(select(VerificationToken)).one().used_at is None
