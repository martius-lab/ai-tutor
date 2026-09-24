#!/usr/bin/env python3
"""Fill an (empty) AI Tutor database with dummy data for manual testing.

Creates a handful of users covering the different permission levels, two lectures
(one of them with a custom prompt set as its default), a few exercises, some
example conversations/submissions and reports, plus a spare lecturer
registration token.

Meant to be run once against a fresh database, e.g. right after
``uv run reflex db migrate``.  It is idempotent: existing rows are recognized by
their natural key (username, lecture name, ...) and left untouched, so running the
script again just fills in whatever is still missing.

The database connection is taken from the Reflex configuration in ``rxconfig.py``
(overridable with ``--db-url`` or the ``REFLEX_DB_URL`` environment variable), so
the script must be run from the project root:

    uv run ./scripts/seed_demo_data.py
    uv run ./scripts/seed_demo_data.py --db-url sqlite:///reflex_main.db

All created users share the password "1234".
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlmodel import Session

DEMO_PASSWORD = "1234"


def parse_args() -> argparse.Namespace:
    """Parse the command line arguments."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
    )
    parser.add_argument(
        "--db-url",
        help=(
            "Database URL to use instead of the one configured in rxconfig.py"
            " (e.g. 'sqlite:///reflex_main.db')."
        ),
    )
    return parser.parse_args()


def get_or_create_user(
    session: Session,
    *,
    username: str,
    email: str,
    role,
    permissions=(),
) -> int:
    """Return the id of a demo user, creating it (with UserInfo/Permission rows) if
    needed.

    Args:
        session: The database session to use.
        username: Login name of the user.
        email: Email address of the user.
        role: Global ``UserRole`` to store on the user's ``UserInfo``.
        permissions: Global permissions to grant the user.

    Returns:
        The id of the (possibly newly created) ``LocalUser``.
    """
    from reflex_local_auth.user import LocalUser
    from sqlmodel import select

    from aitutor.models import Permission, UserInfo

    existing = session.exec(
        select(LocalUser).where(LocalUser.username == username)
    ).one_or_none()
    if existing is not None:
        print(f"User '{username}' already exists, skipping.")
        assert existing.id is not None
        return existing.id

    local_user = LocalUser(
        username=username,
        password_hash=LocalUser.hash_password(DEMO_PASSWORD),
        enabled=True,
    )
    session.add(local_user)
    session.commit()
    session.refresh(local_user)
    assert local_user.id is not None

    session.add(UserInfo(email=email, role=role, user_id=local_user.id))
    for permission in permissions:
        session.add(Permission(user_id=local_user.id, permission=permission))
    session.commit()

    print(f"Created user '{username}' (email={email}).")
    return local_user.id


def get_or_create_lecture(session: Session, **fields) -> int:
    """Return the id of a lecture, creating it if it doesn't exist yet.

    Args:
        session: The database session to use.
        **fields: Values passed to the ``Lecture`` constructor.  Must include
            ``lecture_name``.

    Returns:
        The id of the (possibly newly created) ``Lecture``.
    """
    from sqlmodel import select

    from aitutor.models import Lecture

    existing = session.exec(
        select(Lecture).where(Lecture.lecture_name == fields["lecture_name"])
    ).one_or_none()
    if existing is not None:
        print(f"Lecture '{fields['lecture_name']}' already exists, skipping.")
        assert existing.id is not None
        return existing.id

    lecture = Lecture(**fields)
    session.add(lecture)
    session.commit()
    session.refresh(lecture)
    assert lecture.id is not None

    print(f"Created lecture '{lecture.lecture_name}'.")
    return lecture.id


def ensure_membership(session: Session, *, lecture_id: int, user_id: int, role) -> None:
    """Make sure a user is a member of a lecture with (at least) the given role."""
    from sqlmodel import select

    from aitutor.models import LinkUserLecture

    existing = session.exec(
        select(LinkUserLecture).where(
            LinkUserLecture.lecture_id == lecture_id,
            LinkUserLecture.user_id == user_id,
        )
    ).one_or_none()
    if existing is not None:
        return

    session.add(LinkUserLecture(lecture_id=lecture_id, user_id=user_id, role=role))
    session.commit()


def get_or_create_prompt(session: Session, *, name: str, lecture_id, **fields) -> int:
    """Return the id of a prompt (scoped to a lecture or global), creating it if
    needed.
    """
    from sqlmodel import select

    from aitutor.models import Prompt

    existing = session.exec(
        select(Prompt).where(Prompt.name == name, Prompt.lecture_id == lecture_id)
    ).one_or_none()
    if existing is not None:
        assert existing.id is not None
        return existing.id

    prompt = Prompt(name=name, lecture_id=lecture_id, **fields)
    session.add(prompt)
    session.commit()
    session.refresh(prompt)
    assert prompt.id is not None

    print(f"Created prompt '{name}'.")
    return prompt.id


def get_or_create_exercise(session: Session, *, title: str, lecture_id: int, **fields):
    """Return an exercise for a lecture, creating it if it doesn't exist yet."""
    from sqlmodel import select

    from aitutor.models import Exercise

    existing = session.exec(
        select(Exercise).where(
            Exercise.title == title, Exercise.lecture_id == lecture_id
        )
    ).one_or_none()
    if existing is not None:
        return existing

    exercise = Exercise(title=title, lecture_id=lecture_id, **fields)
    session.add(exercise)
    session.commit()
    session.refresh(exercise)

    print(f"Created exercise '{title}'.")
    return exercise


def get_or_create_tag(session: Session, *, name: str, lecture_id: int):
    """Return a tag for a lecture, creating it if it doesn't exist yet."""
    from sqlmodel import select

    from aitutor.models import Tag

    existing = session.exec(
        select(Tag).where(Tag.name == name, Tag.lecture_id == lecture_id)
    ).one_or_none()
    if existing is not None:
        return existing

    tag = Tag(name=name, lecture_id=lecture_id)
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


def make_conversation(exercise_title: str, description: str) -> list[dict]:
    """Build a small, realistic looking chat transcript for an exercise."""
    return [
        {
            "role": "system",
            "content": (
                f'You pretend to be a learner trying to understand "{description}".'
                f' The student will explain "{exercise_title}" to you.'
            ),
            "check_passed": False,
        },
        {
            "role": "assistant",
            "content": f"Hi! Could you explain {description} to me?",
            "check_passed": False,
        },
        {
            "role": "user",
            "content": (
                f"Sure. {description} basically means breaking the problem down"
                " into smaller steps and solving each one in order."
            ),
            "check_passed": False,
        },
        {
            "role": "assistant",
            "content": "That makes sense, thanks! Could you give a short example?",
            "check_passed": False,
        },
        {
            "role": "user",
            "content": (
                "For example, sorting a list by repeatedly picking the smallest"
                " remaining element."
            ),
            "check_passed": False,
        },
    ]


def get_or_create_exercise_result(
    session: Session,
    *,
    exercise_id: int,
    userinfo_id: int,
    conversation: list[dict],
    submitted: bool,
    check_passed: bool,
    days_ago: int,
    tokens_used: int,
):
    """Return an exercise result for a user/exercise pair, creating it if needed."""
    from zoneinfo import ZoneInfo

    from sqlmodel import select

    from aitutor.global_vars import TIME_ZONE
    from aitutor.models import ExerciseResult

    existing = session.exec(
        select(ExerciseResult).where(
            ExerciseResult.exercise_id == exercise_id,
            ExerciseResult.userinfo_id == userinfo_id,
        )
    ).one_or_none()
    if existing is not None:
        return existing

    finished_conversation = []
    submit_time_stamp = None
    if submitted:
        check_result_message = {
            "role": "check_result",
            "content": (
                "Great, that's correct!" if check_passed else "Not quite, try again."
            ),
            "check_passed": check_passed,
        }
        finished_conversation = [*conversation, check_result_message]
        submit_time_stamp = datetime.now(ZoneInfo(TIME_ZONE)) - timedelta(days=days_ago)

    result = ExerciseResult(
        exercise_id=exercise_id,
        userinfo_id=userinfo_id,
        conversation_text=conversation,
        finished_conversation=finished_conversation,
        check_passed=submitted and check_passed,
        submit_time_stamp=submit_time_stamp,
        tokens_used=tokens_used,
    )
    session.add(result)
    session.commit()
    session.refresh(result)
    return result


def get_or_create_report(
    session: Session,
    *,
    exercise_id: int,
    lecture_id: int,
    userinfo_id: int,
    report_text: str,
    conversation_snapshot: list[dict],
    looked_at: bool,
):
    """Return a report for a user/exercise pair, creating it if it doesn't exist yet."""
    from sqlmodel import select

    from aitutor.models import Report

    existing = session.exec(
        select(Report).where(
            Report.exercise_id == exercise_id,
            Report.userinfo_id == userinfo_id,
        )
    ).one_or_none()
    if existing is not None:
        return existing

    report = Report(
        exercise_id=exercise_id,
        lecture_id=lecture_id,
        userinfo_id=userinfo_id,
        report_text=report_text,
        conversation_snapshot=conversation_snapshot,
        looked_at=looked_at,
    )
    session.add(report)
    session.commit()
    print(f"Created report for exercise id={exercise_id}.")
    return report


def seed(session: Session) -> None:
    """Create all demo users, lectures, exercises, submissions and reports."""
    from zoneinfo import ZoneInfo

    from aitutor.global_vars import TIME_ZONE
    from aitutor.models import GlobalPermission, LectureRole, UserRole

    # -- Users, one per permission combination -----------------------------------
    admin_id = get_or_create_user(
        session,
        username="admin.demo",
        email="admin.demo@example.com",
        role=UserRole.ADMIN,
        permissions=[GlobalPermission.ADMIN],
    )
    maintainer_id = get_or_create_user(
        session,
        username="mia.maintainer",
        email="mia.maintainer@example.com",
        role=UserRole.STUDENT,
        permissions=[GlobalPermission.MAINTAINER],
    )
    leo_id = get_or_create_user(
        session,
        username="leo.lecturer",
        email="leo.lecturer@example.com",
        role=UserRole.STUDENT,
        permissions=[GlobalPermission.LECTURER],
    )
    nora_id = get_or_create_user(
        session,
        username="nora.lecturer",
        email="nora.lecturer@example.com",
        role=UserRole.STUDENT,
        permissions=[GlobalPermission.LECTURER],
    )
    tina_id = get_or_create_user(
        session,
        username="tina.tutor",
        email="tina.tutor@example.com",
        role=UserRole.STUDENT,
    )
    alex_id = get_or_create_user(
        session,
        username="alex.student",
        email="alex.student@example.com",
        role=UserRole.STUDENT,
    )
    sam_id = get_or_create_user(
        session,
        username="sam.student",
        email="sam.student@example.com",
        role=UserRole.STUDENT,
    )
    jamie_id = get_or_create_user(
        session,
        username="jamie.student",
        email="jamie.student@example.com",
        role=UserRole.STUDENT,
    )

    # UserInfo ids differ from LocalUser ids; look them up for use as foreign keys
    # on ExerciseResult/Report.
    from sqlmodel import select

    from aitutor.models import UserInfo

    userinfo_id_by_user_id: dict[int, int] = {}
    for row in session.exec(
        select(UserInfo).where(
            UserInfo.user_id.in_(  # type: ignore[attr-defined]
                [
                    admin_id,
                    maintainer_id,
                    leo_id,
                    nora_id,
                    tina_id,
                    alex_id,
                    sam_id,
                    jamie_id,
                ]
            )
        )
    ).all():
        assert row.id is not None
        userinfo_id_by_user_id[row.user_id] = row.id

    # -- Lecture 1: "Introduction to Programming", with a custom default prompt --
    intro_lecture_id = get_or_create_lecture(
        session,
        lecture_name="Introduction to Programming",
        lecturer_name="Dr. Leo Lecturer",
        registration_code="intro2026",
        lecture_information_text=(
            "Welcome to Introduction to Programming! This lecture covers the basics"
            " of programming: variables, control flow, functions and simple"
            " algorithms."
        ),
        check_conversation_prompt=(
            "Check whether the student correctly explained the given task based on"
            " the conversation so far. Answer with PASS or FAIL and a short"
            " explanation."
        ),
    )
    ensure_membership(
        session, lecture_id=intro_lecture_id, user_id=leo_id, role=LectureRole.OWNER
    )
    ensure_membership(
        session, lecture_id=intro_lecture_id, user_id=tina_id, role=LectureRole.TUTOR
    )
    ensure_membership(
        session, lecture_id=intro_lecture_id, user_id=alex_id, role=LectureRole.STUDENT
    )
    ensure_membership(
        session, lecture_id=intro_lecture_id, user_id=sam_id, role=LectureRole.STUDENT
    )

    custom_prompt_id = get_or_create_prompt(
        session,
        name="Friendly Beginner Tutor",
        lecture_id=intro_lecture_id,
        prompt_template="""
You will act as a friendly learning assistant for absolute beginners.
Using the inverted teaching methods, a student is given the task to explain
"{title}" with description "{description}"
Lesson context provided by the teacher:
--------------------------
{lesson_context}
--------------------------
Pretend to be a learner trying to understand {description}. Keep your tone
encouraging and simple, avoid jargon, and give small hints instead of the
answer if the student struggles.
""",
    )
    with session.no_autoflush:
        from aitutor.models import Lecture

        lecture = session.get(Lecture, intro_lecture_id)
        if lecture is not None and lecture.default_prompt_id is None:
            lecture.default_prompt_id = custom_prompt_id
            session.add(lecture)
            session.commit()
            print("Set custom prompt as default for 'Introduction to Programming'.")

    basics_tag = get_or_create_tag(session, name="basics", lecture_id=intro_lecture_id)
    mandatory_tag = get_or_create_tag(
        session, name="mandatory", lecture_id=intro_lecture_id
    )
    optional_tag = get_or_create_tag(
        session, name="optional", lecture_id=intro_lecture_id
    )

    now = datetime.now(ZoneInfo(TIME_ZONE))

    ex_variables = get_or_create_exercise(
        session,
        title="Variables and Data Types",
        lecture_id=intro_lecture_id,
        description="What a variable is and how data types differ.",
        lesson_context=(
            "A variable is a named location in memory used to store a value."
            " Python has several built-in data types: int, float, str, bool, ..."
        ),
        prompt_id=custom_prompt_id,
    )
    ex_variables.tags = [basics_tag, mandatory_tag]
    session.add(ex_variables)

    ex_loops = get_or_create_exercise(
        session,
        title="For Loops",
        lecture_id=intro_lecture_id,
        description="How a for loop repeats code for each element of a sequence.",
        lesson_context="A for loop iterates over the elements of an iterable, ...",
        deadline=now + timedelta(days=10),
        days_to_complete=14,
        prompt_id=custom_prompt_id,
    )
    ex_loops.tags = [mandatory_tag]
    session.add(ex_loops)

    ex_recursion = get_or_create_exercise(
        session,
        title="Recursion (bonus)",
        lecture_id=intro_lecture_id,
        description="How a function can call itself to solve smaller subproblems.",
        lesson_context="Recursion consists of a base case and a recursive case, ...",
        is_hidden=True,
        prompt_id=custom_prompt_id,
    )
    ex_recursion.tags = [optional_tag]
    session.add(ex_recursion)
    session.commit()

    # -- Lecture 2: "Data Structures & Algorithms", using the global default prompt --
    dsa_lecture_id = get_or_create_lecture(
        session,
        lecture_name="Data Structures & Algorithms",
        lecturer_name="Prof. Nora Lecturer",
        registration_code="dsa2026",
        lecture_information_text=(
            "This lecture builds on Introduction to Programming and covers common"
            " data structures (lists, stacks, trees, graphs) and algorithms"
            " (sorting, searching)."
        ),
        check_conversation_prompt=(
            "Check whether the student correctly explained the given task based on"
            " the conversation so far. Answer with PASS or FAIL and a short"
            " explanation."
        ),
    )
    ensure_membership(
        session, lecture_id=dsa_lecture_id, user_id=nora_id, role=LectureRole.OWNER
    )
    ensure_membership(
        session, lecture_id=dsa_lecture_id, user_id=tina_id, role=LectureRole.TUTOR
    )
    ensure_membership(
        session, lecture_id=dsa_lecture_id, user_id=jamie_id, role=LectureRole.STUDENT
    )

    dsa_tag = get_or_create_tag(session, name="sorting", lecture_id=dsa_lecture_id)

    from aitutor.models import Prompt

    global_prompt = session.exec(
        select(Prompt).where(Prompt.lecture_id == None)
    ).first()
    assert global_prompt is not None and global_prompt.id is not None
    global_prompt_id = global_prompt.id

    ex_sorting = get_or_create_exercise(
        session,
        title="Sorting Algorithms",
        lecture_id=dsa_lecture_id,
        description="How bubble sort and selection sort work and how they compare.",
        lesson_context=(
            "Sorting algorithms rearrange elements into a defined order, ..."
        ),
        prompt_id=global_prompt_id,
    )
    ex_sorting.tags = [dsa_tag]
    session.add(ex_sorting)

    ex_stacks = get_or_create_exercise(
        session,
        title="Stacks and Queues",
        lecture_id=dsa_lecture_id,
        description="The difference between LIFO and FIFO data structures.",
        lesson_context="A stack supports push/pop at one end (LIFO), a queue ...",
        prompt_id=global_prompt_id,
    )
    session.add(ex_stacks)
    session.commit()

    assert ex_variables.id is not None
    assert ex_loops.id is not None
    assert ex_recursion.id is not None
    assert ex_sorting.id is not None
    assert ex_stacks.id is not None

    # -- Submissions / conversations ----------------------------------------------
    get_or_create_exercise_result(
        session,
        exercise_id=ex_variables.id,
        userinfo_id=userinfo_id_by_user_id[alex_id],
        conversation=make_conversation(ex_variables.title, ex_variables.description),
        submitted=True,
        check_passed=True,
        days_ago=5,
        tokens_used=1_240,
    )
    get_or_create_exercise_result(
        session,
        exercise_id=ex_variables.id,
        userinfo_id=userinfo_id_by_user_id[sam_id],
        conversation=make_conversation(ex_variables.title, ex_variables.description),
        submitted=True,
        check_passed=False,
        days_ago=3,
        tokens_used=980,
    )
    get_or_create_exercise_result(
        session,
        exercise_id=ex_loops.id,
        userinfo_id=userinfo_id_by_user_id[alex_id],
        conversation=make_conversation(ex_loops.title, ex_loops.description)[:3],
        submitted=False,
        check_passed=False,
        days_ago=0,
        tokens_used=410,
    )
    get_or_create_exercise_result(
        session,
        exercise_id=ex_sorting.id,
        userinfo_id=userinfo_id_by_user_id[jamie_id],
        conversation=make_conversation(ex_sorting.title, ex_sorting.description),
        submitted=True,
        check_passed=True,
        days_ago=1,
        tokens_used=1_560,
    )

    # -- Reports --------------------------------------------------------------
    get_or_create_report(
        session,
        exercise_id=ex_loops.id,
        lecture_id=intro_lecture_id,
        userinfo_id=userinfo_id_by_user_id[alex_id],
        report_text=(
            "The AI tutor keeps insisting my answer is wrong even though I'm"
            " pretty sure it's correct. Could a tutor take a look?"
        ),
        conversation_snapshot=make_conversation(ex_loops.title, ex_loops.description),
        looked_at=False,
    )
    get_or_create_report(
        session,
        exercise_id=ex_variables.id,
        lecture_id=intro_lecture_id,
        userinfo_id=userinfo_id_by_user_id[sam_id],
        report_text=(
            "The exercise description seems to have a typo in the second sentence."
        ),
        conversation_snapshot=make_conversation(
            ex_variables.title, ex_variables.description
        ),
        looked_at=True,
    )

    # -- Spare lecturer registration token ------------------------------------
    from sqlmodel import select as select_

    from aitutor.models import LecturerRegistrationToken

    existing_token = session.exec(
        select_(LecturerRegistrationToken).where(
            LecturerRegistrationToken.token == "demo-lecturer-token"
        )
    ).one_or_none()
    if existing_token is None:
        session.add(
            LecturerRegistrationToken(
                token="demo-lecturer-token",
                created_by=admin_id,
                created_at=now,
                expires_at=now + timedelta(days=30),
            )
        )
        session.commit()
        print("Created spare lecturer registration token 'demo-lecturer-token'.")


def adjust_defaults(session: Session) -> None:
    """Adjust default values (admin password and registration code).

    The initial admin password and registration code are randomly generated.  To make
    testing easier, we set both to DEMO_PASSWORD here.
    """
    from sqlmodel import select

    from aitutor.models import Config, LocalUser

    admin = session.exec(
        select(LocalUser).where(LocalUser.username == "admin")
    ).one_or_none()
    if admin is not None:
        admin.password_hash = LocalUser.hash_password(DEMO_PASSWORD)
        print("Set admin password to DEMO_PASSWORD.")

    if config := session.get(Config, 1):
        config.registration_code = DEMO_PASSWORD
        print("Set default registration code to DEMO_PASSWORD.")

    session.commit()


def main() -> int:
    """Run the script."""
    args = parse_args()

    if args.db_url:
        # Reflex' config can be overwritten via environment variables.  This needs to
        # happen before reflex is imported below.
        os.environ["REFLEX_DB_URL"] = args.db_url

    # Imported here, so the REFLEX_DB_URL override above is picked up and the script
    # can print its help without loading the (slow) reflex imports.
    import reflex as rx

    from aitutor.utilities.first_setup import first_time_setup

    first_time_setup()

    with rx.session() as session:
        url = session.get_bind().engine.url
        print(f"Database: {url.render_as_string(hide_password=True)}")
        adjust_defaults(session)
        seed(session)

    print("\nDone. All demo users share the password '1234':")
    for username in (
        "admin.demo",
        "mia.maintainer",
        "leo.lecturer",
        "nora.lecturer",
        "tina.tutor",
        "alex.student",
        "sam.student",
        "jamie.student",
    ):
        print(f"  - {username}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
