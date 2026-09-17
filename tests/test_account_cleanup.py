from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from reflex_local_auth.auth_session import LocalAuthSession
from reflex_local_auth.user import LocalUser
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine, select

from aitutor.account_cleanup import delete_unverified_accounts, purge_expired_tokens
from aitutor.global_vars import (
    TIME_ZONE,
    UNVERIFIED_ACCOUNT_RETENTION,
    VERIFICATION_TOKEN_VALIDITY,
)
from aitutor.models import (
    Lecture,
    LectureRole,
    LinkUserLecture,
    UserInfo,
    UserRole,
    VerificationPurpose,
    VerificationToken,
)
from aitutor.verification import issue_token

NOW = datetime(2026, 9, 16, 12, 0, tzinfo=ZoneInfo(TIME_ZONE))


@pytest.fixture
def session():
    engine = create_engine("sqlite://")

    # Deleting an account relies on ON DELETE CASCADE (as on PostgreSQL), which SQLite
    # only enforces with foreign keys enabled.
    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, connection_record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def make_user(session, username, *, verified, created_at):
    local_user = LocalUser(
        username=username, password_hash=LocalUser.hash_password("secret")
    )
    session.add(local_user)
    session.commit()
    session.refresh(local_user)
    assert local_user.id is not None

    session.add(
        UserInfo(
            user_id=local_user.id,
            email=f"{username}@example.com",
            role=UserRole.STUDENT,
            verified=verified,
            created_at=created_at,
        )
    )
    session.commit()
    return local_user.id


def usernames(session):
    return {user.username for user in session.exec(select(LocalUser)).all()}


# purge_expired_tokens -----------------------------------------------------------------


def make_local_users(session, count):
    """Create the users the tokens belong to, with IDs 1 to count."""
    for i in range(1, count + 1):
        session.add(LocalUser(id=i, username=f"user{i}", password_hash=b""))
    session.commit()


def expire(session, user_id, purpose=VerificationPurpose.EMAIL):
    token = session.exec(
        select(VerificationToken).where(
            VerificationToken.user_id == user_id, VerificationToken.purpose == purpose
        )
    ).one()
    token.expires_at = NOW - timedelta(seconds=1)
    session.commit()


def test_purge_keeps_valid_tokens(session):
    make_local_users(session, 1)
    issue_token(session, user_id=1, email="a@example.com")
    session.commit()

    assert purge_expired_tokens(session) == 0
    session.commit()

    assert len(session.exec(select(VerificationToken)).all()) == 1


def test_purge_deletes_expired_tokens_only(session):
    make_local_users(session, 3)
    issue_token(session, user_id=1, email="a@example.com")
    issue_token(session, user_id=2, email="b@example.com")
    issue_token(
        session,
        user_id=3,
        email="c@example.com",
        purpose=VerificationPurpose.PASSWORD_RESET,
    )
    session.commit()
    expire(session, 1)
    expire(session, 3, VerificationPurpose.PASSWORD_RESET)

    assert purge_expired_tokens(session, now=NOW) == 2
    session.commit()

    remaining = session.exec(select(VerificationToken)).all()
    assert [token.user_id for token in remaining] == [2]


def test_purge_deletes_used_tokens_after_expiry(session):
    make_local_users(session, 1)
    issue_token(session, user_id=1, email="a@example.com")
    session.commit()
    token = session.exec(select(VerificationToken)).one()
    token.used_at = NOW - VERIFICATION_TOKEN_VALIDITY
    session.commit()
    expire(session, 1)

    assert purge_expired_tokens(session, now=NOW) == 1


def test_purge_handles_naive_datetimes_from_sqlite(session):
    # SQLite drops the time zone.  A token that expired one hour ago in TIME_ZONE must
    # be purged no matter what the time zone of the host is.
    make_local_users(session, 1)
    issue_token(session, user_id=1, email="a@example.com")
    session.commit()
    token = session.exec(select(VerificationToken)).one()
    token.expires_at = NOW - timedelta(hours=1)
    session.commit()
    session.expire_all()

    assert session.exec(select(VerificationToken)).one().expires_at.tzinfo is None
    assert purge_expired_tokens(session, now=NOW) == 1


def test_purge_with_reference_time_in_another_time_zone(session):
    # SQLite drops the time zone of the reference time without converting it, so a
    # reference time in UTC must be converted to TIME_ZONE first.
    make_local_users(session, 4)
    for user_id, minutes in enumerate([-90, -30, 30, 90], start=1):
        issue_token(session, user_id=user_id, email=f"{user_id}@example.com")
        session.commit()
        token = session.exec(
            select(VerificationToken).where(VerificationToken.user_id == user_id)
        ).one()
        token.expires_at = NOW + timedelta(minutes=minutes)
        session.commit()

    assert purge_expired_tokens(session, now=NOW.astimezone(timezone.utc)) == 2
    session.commit()

    remaining = session.exec(select(VerificationToken)).all()
    assert sorted(token.user_id for token in remaining) == [3, 4]


def test_purge_rejects_naive_reference_time(session):
    with pytest.raises(ValueError):
        purge_expired_tokens(session, now=NOW.replace(tzinfo=None))


# delete_unverified_accounts -----------------------------------------------------------


def test_deletes_old_unverified_account(session):
    user_id = make_user(
        session,
        "old",
        verified=False,
        created_at=NOW - UNVERIFIED_ACCOUNT_RETENTION - timedelta(minutes=1),
    )
    issue_token(session, user_id=user_id, email="old@example.com")
    session.add(LocalAuthSession(user_id=user_id, session_id="abc", expiration=NOW))
    session.commit()

    result = delete_unverified_accounts(session, now=NOW)
    session.commit()

    assert [account.username for account in result.deleted] == ["old"]
    assert result.skipped_sole_lecture_owner == []
    assert usernames(session) == set()
    assert session.exec(select(UserInfo)).all() == []
    assert session.exec(select(VerificationToken)).all() == []
    assert session.exec(select(LocalAuthSession)).all() == []


def test_keeps_young_unverified_account(session):
    make_user(
        session,
        "young",
        verified=False,
        created_at=NOW - UNVERIFIED_ACCOUNT_RETENTION + timedelta(minutes=1),
    )

    result = delete_unverified_accounts(session, now=NOW)
    session.commit()

    assert result.deleted == []
    assert usernames(session) == {"young"}


def test_keeps_old_verified_account(session):
    make_user(session, "verified", verified=True, created_at=NOW - timedelta(days=365))

    result = delete_unverified_accounts(session, now=NOW)
    session.commit()

    assert result.deleted == []
    assert usernames(session) == {"verified"}


def test_only_affects_due_accounts(session):
    old = NOW - UNVERIFIED_ACCOUNT_RETENTION - timedelta(days=1)
    make_user(session, "due1", verified=False, created_at=old)
    make_user(session, "verified", verified=True, created_at=old)
    make_user(session, "young", verified=False, created_at=NOW)
    make_user(session, "due2", verified=False, created_at=old)

    result = delete_unverified_accounts(session, now=NOW)
    session.commit()

    assert [account.username for account in result.deleted] == ["due1", "due2"]
    assert usernames(session) == {"verified", "young"}


def test_keeps_sole_lecture_owner(session):
    old = NOW - UNVERIFIED_ACCOUNT_RETENTION - timedelta(days=1)
    sole_owner = make_user(session, "sole_owner", verified=False, created_at=old)
    co_owner = make_user(session, "co_owner", verified=False, created_at=old)
    other = make_user(session, "other", verified=True, created_at=old)

    lecture1 = Lecture(lecture_name="Lecture 1")
    lecture2 = Lecture(lecture_name="Lecture 2")
    session.add(lecture1)
    session.add(lecture2)
    session.commit()
    session.add(
        LinkUserLecture(
            lecture_id=lecture1.id, user_id=sole_owner, role=LectureRole.OWNER
        )
    )
    session.add(
        LinkUserLecture(
            lecture_id=lecture2.id, user_id=co_owner, role=LectureRole.OWNER
        )
    )
    session.add(
        LinkUserLecture(lecture_id=lecture2.id, user_id=other, role=LectureRole.OWNER)
    )
    session.commit()

    result = delete_unverified_accounts(session, now=NOW)
    session.commit()

    assert [account.username for account in result.deleted] == ["co_owner"]
    assert [a.username for a in result.skipped_sole_lecture_owner] == ["sole_owner"]
    assert usernames(session) == {"sole_owner", "other"}


def test_delete_with_reference_time_in_another_time_zone(session):
    # see test_purge_with_reference_time_in_another_time_zone
    cutoff = NOW - UNVERIFIED_ACCOUNT_RETENTION
    make_user(
        session, "due1", verified=False, created_at=cutoff - timedelta(minutes=90)
    )
    make_user(
        session, "due2", verified=False, created_at=cutoff - timedelta(minutes=30)
    )
    make_user(
        session, "young1", verified=False, created_at=cutoff + timedelta(minutes=30)
    )
    make_user(
        session, "young2", verified=False, created_at=cutoff + timedelta(minutes=90)
    )

    result = delete_unverified_accounts(session, now=NOW.astimezone(timezone.utc))
    session.commit()

    assert [account.username for account in result.deleted] == ["due1", "due2"]
    assert usernames(session) == {"young1", "young2"}


def test_delete_rejects_naive_reference_time(session):
    with pytest.raises(ValueError):
        delete_unverified_accounts(session, now=NOW.replace(tzinfo=None))
