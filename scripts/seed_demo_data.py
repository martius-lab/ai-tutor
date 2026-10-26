#!/usr/bin/env python3
"""Fill an (empty) AI Tutor database with dummy data for manual testing.

Creates a handful of users covering the different permission levels, two lectures
(one of them with a custom prompt set as its default), a few exercises, some
example conversations/submissions and reports, plus a spare lecturer
registration token.  The data is defined in ``USERS``, ``LECTURES`` and
``LECTURER_TOKENS`` at the top of this script.

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
from typing import TYPE_CHECKING, Any, Literal, NotRequired, TypedDict

if TYPE_CHECKING:
    from sqlmodel import Session, SQLModel

DEMO_PASSWORD = "1234"


# -- Data types -------------------------------------------------------------------
# Enum values are given by their member name (e.g. "OWNER" for LectureRole.OWNER),
# so aitutor.models doesn't need to be imported at module level.

type GlobalPermissionName = Literal["LECTURER", "MAINTAINER", "ADMIN"]
type LectureRoleName = Literal["STUDENT", "TUTOR", "OWNER"]
type Message = dict[str, Any]


class SeedUser(TypedDict):
    """A demo user."""

    username: str
    email: str
    verified: bool
    permissions: NotRequired[list[GlobalPermissionName]]
    # Unconfirmed new email address.  Requires ``verified``.
    pending_email: NotRequired[str]


class SeedPrompt(TypedDict):
    """A lecture-specific prompt."""

    name: str
    prompt_template: str


class SeedExerciseResult(TypedDict):
    """A user's conversation for an exercise, possibly submitted."""

    username: str
    submitted: bool
    check_passed: bool
    days_ago: int
    tokens_used: int
    # Defaults to the template from make_conversation().
    conversation: NotRequired[list[Message]]
    # Only use the first n messages of the conversation.
    conversation_length: NotRequired[int]


class SeedReport(TypedDict):
    """A report a user filed for an exercise."""

    username: str
    report_text: str
    looked_at: bool
    # Defaults to the template from make_conversation().
    conversation: NotRequired[list[Message]]
    # Only use the first n messages of the conversation.
    conversation_length: NotRequired[int]


class SeedExercise(TypedDict):
    """An exercise of a lecture, including results and reports for it."""

    title: str
    description: str
    lesson_context: str
    tags: NotRequired[list[str]]
    is_hidden: NotRequired[bool]
    # Relative to the time the script is run.
    deadline: NotRequired[timedelta]
    days_to_complete: NotRequired[int]
    results: NotRequired[list[SeedExerciseResult]]
    reports: NotRequired[list[SeedReport]]


class SeedLecture(TypedDict):
    """A lecture with its members and exercises."""

    lecture_name: str
    lecturer_name: str
    registration_code: str
    lecture_information_text: str
    check_conversation_prompt: str
    members: dict[str, LectureRoleName]
    # Used for all exercises of the lecture.  If not set, the global default prompt
    # is used.
    default_prompt: NotRequired[SeedPrompt]
    exercises: list[SeedExercise]


class SeedLecturerToken(TypedDict):
    """A lecturer registration token."""

    token: str
    created_by: str
    valid_for: timedelta


# -- Data ---------------------------------------------------------------------------

USERS: list[SeedUser] = [
    {
        "username": "admin.demo",
        "email": "admin.demo@example.com",
        "verified": True,
        "permissions": ["ADMIN"],
    },
    {
        "username": "mia.maintainer",
        "email": "mia.maintainer@example.com",
        "verified": True,
        "permissions": ["MAINTAINER"],
    },
    {
        "username": "leo.lecturer",
        "email": "leo.lecturer@example.com",
        "verified": True,
        "permissions": ["LECTURER"],
    },
    {
        "username": "nora.lecturer",
        "email": "nora.lecturer@example.com",
        "verified": True,
        "permissions": ["LECTURER"],
    },
    {
        "username": "tina.tutor",
        "email": "tina.tutor@example.com",
        "verified": True,
    },
    {
        "username": "alex.student",
        "email": "alex.student@example.com",
        "verified": True,
    },
    {
        "username": "sam.student",
        "email": "sam.student@example.com",
        "verified": True,
    },
    {
        "username": "jamie.student",
        "email": "jamie.student@example.com",
        "verified": True,
        "pending_email": "jamie.new@example.com",
    },
    {
        "username": "unverified.student",
        "email": "unverified.student@example.com",
        "verified": False,
    },
]

CHECK_CONVERSATION_PROMPT = (
    "Check whether the student correctly explained the given task based on"
    " the conversation so far. Answer with PASS or FAIL and a short"
    " explanation."
)

LECTURES: list[SeedLecture] = [
    {
        "lecture_name": "Introduction to Programming",
        "lecturer_name": "Dr. Leo Lecturer",
        "registration_code": "intro2026",
        "lecture_information_text": (
            "Welcome to Introduction to Programming! This lecture covers the basics"
            " of programming: variables, control flow, functions and simple"
            " algorithms."
        ),
        "check_conversation_prompt": CHECK_CONVERSATION_PROMPT,
        "members": {
            "leo.lecturer": "OWNER",
            "tina.tutor": "TUTOR",
            "alex.student": "STUDENT",
            "sam.student": "STUDENT",
        },
        "default_prompt": {
            "name": "Friendly Beginner Tutor",
            "prompt_template": """
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
        },
        "exercises": [
            {
                "title": "Variables and Data Types",
                "description": "What a variable is and how data types differ.",
                "lesson_context": (
                    "A variable is a named location in memory used to store a"
                    " value. Python has several built-in data types: int, float,"
                    " str, bool, ..."
                ),
                "tags": ["basics", "mandatory"],
                "results": [
                    {
                        "username": "alex.student",
                        "submitted": True,
                        "check_passed": True,
                        "days_ago": 5,
                        "tokens_used": 1_240,
                    },
                    {
                        "username": "sam.student",
                        "submitted": True,
                        "check_passed": False,
                        "days_ago": 3,
                        "tokens_used": 980,
                    },
                ],
                "reports": [
                    {
                        "username": "sam.student",
                        "report_text": (
                            "The exercise description seems to have a typo in the"
                            " second sentence."
                        ),
                        "looked_at": True,
                    },
                ],
            },
            {
                "title": "For Loops",
                "description": (
                    "How a for loop repeats code for each element of a sequence."
                ),
                "lesson_context": (
                    "A for loop iterates over the elements of an iterable, ..."
                ),
                "tags": ["mandatory"],
                "deadline": timedelta(days=10),
                "days_to_complete": 14,
                "results": [
                    {
                        "username": "alex.student",
                        "submitted": False,
                        "check_passed": False,
                        "days_ago": 0,
                        "tokens_used": 410,
                        "conversation_length": 3,
                    },
                ],
                "reports": [
                    {
                        "username": "alex.student",
                        "report_text": (
                            "The AI tutor keeps insisting my answer is wrong even"
                            " though I'm pretty sure it's correct. Could a tutor"
                            " take a look?"
                        ),
                        "looked_at": False,
                    },
                ],
            },
            {
                "title": "Recursion (bonus)",
                "description": (
                    "How a function can call itself to solve smaller subproblems."
                ),
                "lesson_context": (
                    "Recursion consists of a base case and a recursive case, ..."
                ),
                "tags": ["optional"],
                "is_hidden": True,
            },
        ],
    },
    {
        "lecture_name": "Data Structures & Algorithms",
        "lecturer_name": "Prof. Nora Lecturer",
        "registration_code": "dsa2026",
        "lecture_information_text": (
            "This lecture builds on Introduction to Programming and covers common"
            " data structures (lists, stacks, trees, graphs) and algorithms"
            " (sorting, searching)."
        ),
        "check_conversation_prompt": CHECK_CONVERSATION_PROMPT,
        "members": {
            "nora.lecturer": "OWNER",
            "tina.tutor": "TUTOR",
            "jamie.student": "STUDENT",
        },
        "exercises": [
            {
                "title": "Sorting Algorithms",
                "description": (
                    "How bubble sort and selection sort work and how they compare."
                ),
                "lesson_context": (
                    "Sorting algorithms rearrange elements into a defined order, ..."
                ),
                "tags": ["sorting"],
                "results": [
                    {
                        "username": "jamie.student",
                        "submitted": True,
                        "check_passed": True,
                        "days_ago": 1,
                        "tokens_used": 1_560,
                    },
                ],
            },
            {
                "title": "Stacks and Queues",
                "description": "The difference between LIFO and FIFO data structures.",
                "lesson_context": (
                    "A stack supports push/pop at one end (LIFO), a queue ..."
                ),
            },
        ],
    },
]

LECTURER_TOKENS: list[SeedLecturerToken] = [
    {
        "token": "demo-lecturer-token",
        "created_by": "admin.demo",
        "valid_for": timedelta(days=30),
    },
]


# -- Implementation -----------------------------------------------------------------


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


def get_or_create[ModelT: SQLModel](
    session: Session,
    model: type[ModelT],
    key: dict[str, Any],
    label: str | None = None,
    **values: Any,
) -> ModelT:
    """Return the row of ``model`` matching ``key``, creating it if needed.

    Args:
        session: The database session to use.
        model: The model class.
        key: Column values identifying the row.
        label: If set, print a message using this label when the row is created.
        **values: Additional column values used when creating the row.

    Returns:
        The existing or newly created row.
    """
    from sqlmodel import select

    existing = session.exec(
        select(model).where(*(getattr(model, k) == v for k, v in key.items()))
    ).one_or_none()
    if existing is not None:
        return existing

    row = model(**key, **values)
    session.add(row)
    session.commit()
    session.refresh(row)
    if label is not None:
        print(f"Created {label}.")
    return row


def seed_user(session: Session, user: SeedUser) -> tuple[int, int]:
    """Create a demo user (with UserInfo/Permission rows) if it doesn't exist yet.

    Returns:
        The ids of the user's ``LocalUser`` and ``UserInfo``.
    """
    from reflex_local_auth.user import LocalUser
    from sqlmodel import select

    from aitutor.models import GlobalPermission, Permission, UserInfo
    from aitutor.routes import VERIFY_EMAIL
    from aitutor.verification import issue_token

    username = user["username"]
    local_user = session.exec(
        select(LocalUser).where(LocalUser.username == username)
    ).one_or_none()
    if local_user is None:
        local_user = LocalUser(
            username=username,
            password_hash=LocalUser.hash_password(DEMO_PASSWORD),
            enabled=True,
        )
        session.add(local_user)
        session.commit()
        session.refresh(local_user)
        assert local_user.id is not None

        session.add(
            UserInfo(
                email=user["email"],
                verified=user["verified"],
                user_id=local_user.id,
            )
        )
        for permission in user.get("permissions", []):
            session.add(
                Permission(
                    user_id=local_user.id, permission=GlobalPermission[permission]
                )
            )
        session.commit()
        print(f"Created user '{username}' (email={user['email']}).")

        if pending_email := user.get("pending_email"):
            assert user["verified"], "Pending email changes require a verified user."
            token = issue_token(session, user_id=local_user.id, email=pending_email)
            session.commit()
            print(
                f"  Pending email change to {pending_email}:"
                f" {VERIFY_EMAIL}?token={token}"
            )
    else:
        print(f"User '{username}' already exists, skipping.")

    assert local_user.id is not None
    userinfo = session.exec(
        select(UserInfo).where(UserInfo.user_id == local_user.id)
    ).one()
    assert userinfo.id is not None
    return local_user.id, userinfo.id


def make_conversation(exercise_title: str, description: str) -> list[Message]:
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


def get_conversation(
    entry: SeedExerciseResult | SeedReport, exercise: SeedExercise
) -> list[Message]:
    """Return the conversation of a result/report, falling back to the template."""
    conversation = entry.get("conversation") or make_conversation(
        exercise["title"], exercise["description"]
    )
    return conversation[: entry.get("conversation_length")]


def seed_exercise_result(
    session: Session,
    *,
    exercise_id: int,
    userinfo_id: int,
    result: SeedExerciseResult,
    conversation: list[Message],
    now: datetime,
) -> None:
    """Create an exercise result for a user/exercise pair if it doesn't exist."""
    from aitutor.models import ExerciseResult

    finished_conversation = []
    submit_time_stamp = None
    if result["submitted"]:
        check_result_message = {
            "role": "check_result",
            "content": (
                "Great, that's correct!"
                if result["check_passed"]
                else "Not quite, try again."
            ),
            "check_passed": result["check_passed"],
        }
        finished_conversation = [*conversation, check_result_message]
        submit_time_stamp = now - timedelta(days=result["days_ago"])

    get_or_create(
        session,
        ExerciseResult,
        {"exercise_id": exercise_id, "userinfo_id": userinfo_id},
        conversation_text=conversation,
        finished_conversation=finished_conversation,
        check_passed=result["submitted"] and result["check_passed"],
        submit_time_stamp=submit_time_stamp,
        tokens_used=result["tokens_used"],
    )


def seed_lecture(
    session: Session,
    lecture_data: SeedLecture,
    *,
    user_ids: dict[str, tuple[int, int]],
    global_prompt_id: int,
    now: datetime,
) -> None:
    """Create a lecture with its members, prompt, exercises, results and reports."""
    from aitutor.models import (
        Exercise,
        Lecture,
        LectureRole,
        LinkUserLecture,
        Prompt,
        Report,
        Tag,
    )

    name = lecture_data["lecture_name"]
    lecture = get_or_create(
        session,
        Lecture,
        {"lecture_name": name},
        label=f"lecture '{name}'",
        lecturer_name=lecture_data["lecturer_name"],
        registration_code=lecture_data["registration_code"],
        lecture_information_text=lecture_data["lecture_information_text"],
        check_conversation_prompt=lecture_data["check_conversation_prompt"],
    )
    assert lecture.id is not None

    for username, role in lecture_data["members"].items():
        get_or_create(
            session,
            LinkUserLecture,
            {"lecture_id": lecture.id, "user_id": user_ids[username][0]},
            role=LectureRole[role],
        )

    prompt_id = global_prompt_id
    if prompt_data := lecture_data.get("default_prompt"):
        prompt = get_or_create(
            session,
            Prompt,
            {"name": prompt_data["name"], "lecture_id": lecture.id},
            label=f"prompt '{prompt_data['name']}'",
            prompt_template=prompt_data["prompt_template"],
        )
        assert prompt.id is not None
        prompt_id = prompt.id
        if lecture.default_prompt_id is None:
            lecture.default_prompt_id = prompt_id
            session.add(lecture)
            session.commit()
            print(f"Set prompt '{prompt_data['name']}' as default for '{name}'.")

    for exercise_data in lecture_data["exercises"]:
        exercise = get_or_create(
            session,
            Exercise,
            {"title": exercise_data["title"], "lecture_id": lecture.id},
            label=f"exercise '{exercise_data['title']}'",
            description=exercise_data["description"],
            lesson_context=exercise_data["lesson_context"],
            is_hidden=exercise_data.get("is_hidden", False),
            deadline=(
                now + deadline
                if (deadline := exercise_data.get("deadline")) is not None
                else None
            ),
            days_to_complete=exercise_data.get("days_to_complete"),
            prompt_id=prompt_id,
        )
        assert exercise.id is not None

        if not exercise.tags and (tag_names := exercise_data.get("tags")):
            exercise.tags = [
                get_or_create(session, Tag, {"name": tag, "lecture_id": lecture.id})
                for tag in tag_names
            ]
            session.add(exercise)
            session.commit()

        for result in exercise_data.get("results", []):
            seed_exercise_result(
                session,
                exercise_id=exercise.id,
                userinfo_id=user_ids[result["username"]][1],
                result=result,
                conversation=get_conversation(result, exercise_data),
                now=now,
            )

        for report in exercise_data.get("reports", []):
            get_or_create(
                session,
                Report,
                {
                    "exercise_id": exercise.id,
                    "userinfo_id": user_ids[report["username"]][1],
                },
                label=f"report for exercise '{exercise.title}'",
                lecture_id=lecture.id,
                report_text=report["report_text"],
                conversation_snapshot=get_conversation(report, exercise_data),
                looked_at=report["looked_at"],
            )


def seed(session: Session) -> None:
    """Create all demo users, lectures, exercises, submissions and reports."""
    from zoneinfo import ZoneInfo

    from sqlmodel import select

    from aitutor.global_vars import TIME_ZONE
    from aitutor.models import LecturerRegistrationToken, Prompt

    now = datetime.now(ZoneInfo(TIME_ZONE))

    # Maps username to the ids of the user's LocalUser and UserInfo.
    user_ids = {user["username"]: seed_user(session, user) for user in USERS}

    global_prompt = session.exec(
        select(Prompt).where(Prompt.lecture_id == None)
    ).first()
    assert global_prompt is not None and global_prompt.id is not None

    for lecture in LECTURES:
        seed_lecture(
            session,
            lecture,
            user_ids=user_ids,
            global_prompt_id=global_prompt.id,
            now=now,
        )

    for token in LECTURER_TOKENS:
        get_or_create(
            session,
            LecturerRegistrationToken,
            {"token": token["token"]},
            label=f"lecturer registration token '{token['token']}'",
            created_by=user_ids[token["created_by"]][0],
            created_at=now,
            expires_at=now + token["valid_for"],
        )


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

    print(f"\nDone. All demo users share the password '{DEMO_PASSWORD}':")
    for user in USERS:
        print(f"  - {user['username']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
