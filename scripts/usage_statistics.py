#!/usr/bin/env python3
"""Print usage statistics of an AI Tutor database as JSON.

The output contains only aggregated numbers (no usernames or email addresses):
the number of users and their global permissions and, per lecture, the number of
members by role, exercises, submissions and used tokens.

The database is opened read-only, so the script never modifies it.  Only SQLite
and PostgreSQL are supported.

The database connection is taken from the Reflex configuration in ``rxconfig.py``
(overridable with ``--db-url`` or the ``REFLEX_DB_URL`` environment variable), so
the script must be run from the project root:

    uv run ./scripts/usage_statistics.py
    uv run ./scripts/usage_statistics.py --db-url sqlite:///reflex_main.db > stats.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from typing import TYPE_CHECKING, Any

from aitutor.utilities.scripts import connect_database

if TYPE_CHECKING:
    from sqlmodel import Session


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


def collect_statistics(session: Session) -> dict[str, Any]:
    """Collect the usage statistics from the database."""
    from zoneinfo import ZoneInfo

    from sqlalchemy import func
    from sqlmodel import select

    from aitutor.global_vars import TIME_ZONE
    from aitutor.models import (
        Exercise,
        ExerciseResult,
        GlobalPermission,
        Lecture,
        LectureRole,
        LinkUserLecture,
        LocalUser,
        Permission,
    )

    permission_counts = dict(
        session.exec(
            select(Permission.permission, func.count()).group_by(Permission.permission)
        ).all()
    )

    lectures = []
    for lecture in session.exec(select(Lecture).order_by(Lecture.lecture_name)):
        role_counts = dict(
            session.exec(
                select(LinkUserLecture.role, func.count())
                .where(LinkUserLecture.lecture_id == lecture.id)
                .group_by(LinkUserLecture.role)  # type: ignore
            ).all()
        )
        num_exercises = session.exec(
            select(func.count())
            .select_from(Exercise)
            .where(Exercise.lecture_id == lecture.id)
        ).one()
        # count() of a column only counts non-NULL values, i.e. submitted results.
        num_submissions, tokens_used = session.exec(
            select(
                func.count(ExerciseResult.submit_time_stamp),  # type: ignore
                func.coalesce(func.sum(ExerciseResult.tokens_used), 0),
            )
            .join(Exercise)
            .where(Exercise.lecture_id == lecture.id)
        ).one()
        lectures.append(
            {
                "name": lecture.lecture_name,
                "members": {
                    "total": sum(role_counts.values()),
                    **{role.name: role_counts.get(role, 0) for role in LectureRole},
                },
                "exercises": num_exercises,
                "submissions": num_submissions,
                "tokens_used": tokens_used,
            }
        )

    return {
        "generated_at": datetime.now(ZoneInfo(TIME_ZONE)).isoformat(timespec="seconds"),
        "users": {
            "total": session.exec(select(func.count()).select_from(LocalUser)).one(),
            "global_permissions": {
                permission.name: permission_counts.get(permission, 0)
                for permission in GlobalPermission
            },
        },
        "lectures": {
            "total": len(lectures),
            "items": lectures,
        },
        "tokens_used_total": session.exec(
            select(func.coalesce(func.sum(ExerciseResult.tokens_used), 0))
        ).one(),
    }


def main() -> int:
    """Run the script."""
    args = parse_args()

    try:
        _session = connect_database(db_url_override=args.db_url, read_only=True)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1

    with _session() as session:
        url = session.get_bind().engine.url
        print(f"Database: {url.render_as_string(hide_password=True)}", file=sys.stderr)

        statistics = collect_statistics(session)

    print(json.dumps(statistics, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
