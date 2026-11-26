import pytest
from reflex_local_auth.user import LocalUser
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

from aitutor.models import (
    Lecture,
    LectureRole,
    LinkUserLecture,
)
from aitutor.utilities.accounts import (
    is_sole_owner_of_a_lecture,
)


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


# _is_sole_owner_of_a_lecture ----------------------------------------------------------


def make_local_users(session, count):
    """Create the users the tokens belong to, with IDs 1 to count."""
    for i in range(1, count + 1):
        session.add(LocalUser(id=i, username=f"user{i}", password_hash=b""))
    session.commit()


def make_lectures(session, count):
    """Create lectures with IDs 1 to count."""
    for i in range(1, count + 1):
        session.add(Lecture(id=i, lecture_name=f"Lecture {i}"))
    session.commit()


def link(session, user_id, lecture_id, role):
    session.add(LinkUserLecture(user_id=user_id, lecture_id=lecture_id, role=role))
    session.commit()


def test_sole_owner_without_lectures(session):
    make_local_users(session, 1)

    assert not is_sole_owner_of_a_lecture(session, 1)


def test_sole_owner_of_lecture(session):
    make_local_users(session, 1)
    make_lectures(session, 1)
    link(session, 1, 1, LectureRole.OWNER)

    assert is_sole_owner_of_a_lecture(session, 1)


@pytest.mark.parametrize("role", [LectureRole.STUDENT, LectureRole.TUTOR])
def test_sole_owner_ignores_non_owner_roles_of_user(session, role):
    make_local_users(session, 1)
    make_lectures(session, 1)
    link(session, 1, 1, role)

    assert not is_sole_owner_of_a_lecture(session, 1)


def test_sole_owner_with_co_owner(session):
    make_local_users(session, 2)
    make_lectures(session, 1)
    link(session, 1, 1, LectureRole.OWNER)
    link(session, 2, 1, LectureRole.OWNER)

    assert not is_sole_owner_of_a_lecture(session, 1)
    assert not is_sole_owner_of_a_lecture(session, 2)


@pytest.mark.parametrize("role", [LectureRole.STUDENT, LectureRole.TUTOR])
def test_sole_owner_ignores_non_owner_roles_of_others(session, role):
    make_local_users(session, 2)
    make_lectures(session, 1)
    link(session, 1, 1, LectureRole.OWNER)
    link(session, 2, 1, role)

    assert is_sole_owner_of_a_lecture(session, 1)


def test_sole_owner_ignores_owners_of_other_lectures(session):
    make_local_users(session, 2)
    make_lectures(session, 2)
    link(session, 1, 1, LectureRole.OWNER)
    link(session, 2, 2, LectureRole.OWNER)

    assert is_sole_owner_of_a_lecture(session, 1)


@pytest.mark.parametrize("sole_lecture", [1, 2])
def test_sole_owner_of_one_of_multiple_lectures(session, sole_lecture):
    co_owned_lecture = 3 - sole_lecture
    make_local_users(session, 2)
    make_lectures(session, 2)
    link(session, 1, 1, LectureRole.OWNER)
    link(session, 1, 2, LectureRole.OWNER)
    link(session, 2, co_owned_lecture, LectureRole.OWNER)

    assert is_sole_owner_of_a_lecture(session, 1)


def test_sole_owner_with_co_owners_in_all_lectures(session):
    make_local_users(session, 3)
    make_lectures(session, 2)
    link(session, 1, 1, LectureRole.OWNER)
    link(session, 1, 2, LectureRole.OWNER)
    link(session, 2, 1, LectureRole.OWNER)
    link(session, 3, 2, LectureRole.OWNER)

    assert not is_sole_owner_of_a_lecture(session, 1)
