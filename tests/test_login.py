import pytest
from reflex_local_auth.user import LocalUser
from sqlmodel import Session, SQLModel, create_engine, select

from aitutor.global_vars import PASSWORD_MAX_BYTES
from aitutor.models import UserInfo, UserRole
from aitutor.pages.login_and_registration.state import LoginCheckOutcome, check_login

PASSWORD = "correct horse battery staple"


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def make_user(
    session,
    username="alice",
    *,
    password=PASSWORD,
    enabled=True,
    verified=True,
    with_user_info=True,
):
    local_user = LocalUser(
        username=username,
        password_hash=LocalUser.hash_password(password),
        enabled=enabled,
    )
    session.add(local_user)
    session.commit()
    session.refresh(local_user)
    assert local_user.id is not None

    if with_user_info:
        session.add(
            UserInfo(
                user_id=local_user.id,
                email=f"{username}@example.com",
                role=UserRole.STUDENT,
                verified=verified,
            )
        )
        session.commit()
    return local_user.id


def test_success(session):
    user_id = make_user(session)

    outcome, user_info = check_login(session, "alice", PASSWORD)

    assert outcome == LoginCheckOutcome.SUCCESS
    assert user_info is not None
    assert user_info.user_id == user_id


def test_success_returns_user_info_of_the_right_user(session):
    make_user(session, "alice")
    bob_id = make_user(session, "bob")

    outcome, user_info = check_login(session, "bob", PASSWORD)

    assert outcome == LoginCheckOutcome.SUCCESS
    assert user_info is not None
    assert user_info.user_id == bob_id


def test_does_not_modify_the_database(session):
    make_user(session)

    check_login(session, "alice", PASSWORD)

    assert not session.dirty
    assert not session.new
    assert not session.deleted
    user_info = session.exec(select(UserInfo)).one()
    assert user_info.last_login_at is None


def test_unknown_username(session):
    make_user(session)

    assert check_login(session, "bob", PASSWORD) == (
        LoginCheckOutcome.INVALID_CREDENTIALS,
        None,
    )


def test_wrong_password(session):
    make_user(session)

    assert check_login(session, "alice", "wrong") == (
        LoginCheckOutcome.INVALID_CREDENTIALS,
        None,
    )


def test_password_of_another_user(session):
    make_user(session, "alice", password="alice-password")
    make_user(session, "bob", password="bob-password")

    assert check_login(session, "alice", "bob-password") == (
        LoginCheckOutcome.INVALID_CREDENTIALS,
        None,
    )


def test_empty_password_is_rejected_even_if_it_matches(session):
    make_user(session, password="")

    assert check_login(session, "alice", "") == (
        LoginCheckOutcome.INVALID_CREDENTIALS,
        None,
    )


def test_too_long_password_is_rejected(session):
    # bcrypt only considers the first PASSWORD_MAX_BYTES bytes, so a longer password
    # with the correct prefix must not be accepted.
    password = "a" * PASSWORD_MAX_BYTES
    make_user(session, password=password)

    assert check_login(session, "alice", password)[0] == LoginCheckOutcome.SUCCESS
    assert check_login(session, "alice", password + "a") == (
        LoginCheckOutcome.INVALID_CREDENTIALS,
        None,
    )


def test_too_long_multibyte_password_is_rejected(session):
    # "ä" takes two bytes in UTF-8, so the limit is reached after half the characters
    password = "ä" * (PASSWORD_MAX_BYTES // 2)
    make_user(session, password=password)

    assert check_login(session, "alice", password)[0] == LoginCheckOutcome.SUCCESS
    assert check_login(session, "alice", password + "ä") == (
        LoginCheckOutcome.INVALID_CREDENTIALS,
        None,
    )


def test_username_must_match_exactly(session):
    make_user(session)

    assert check_login(session, "Alice", PASSWORD) == (
        LoginCheckOutcome.INVALID_CREDENTIALS,
        None,
    )


def test_disabled_account(session):
    make_user(session, enabled=False)

    assert check_login(session, "alice", PASSWORD) == (
        LoginCheckOutcome.ACCOUNT_DISABLED,
        None,
    )


def test_not_verified_account(session):
    user_id = make_user(session, verified=False)

    outcome, user_info = check_login(session, "alice", PASSWORD)

    assert outcome == LoginCheckOutcome.ACCOUNT_NOT_VERIFIED
    assert user_info is not None
    assert user_info.user_id == user_id


def test_missing_user_info(session):
    make_user(session, with_user_info=False)

    assert check_login(session, "alice", PASSWORD) == (
        LoginCheckOutcome.INTERNAL_ERROR,
        None,
    )


@pytest.mark.parametrize(
    "account",
    [
        {"enabled": False},
        {"verified": False},
        {"with_user_info": False},
    ],
    ids=["disabled", "not_verified", "missing_user_info"],
)
@pytest.mark.parametrize("password", ["wrong", ""])
def test_wrong_password_reveals_nothing_about_the_account(session, account, password):
    make_user(session, **account)

    assert check_login(session, "alice", password) == (
        LoginCheckOutcome.INVALID_CREDENTIALS,
        None,
    )
