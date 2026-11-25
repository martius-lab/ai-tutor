#!/usr/bin/env python3
"""Get list of user email addresses."""

import argparse
import contextlib
import sys

from sqlmodel import select

from aitutor.utilities.scripts import connect_database


def parse_args() -> argparse.Namespace:
    """Parse the command line arguments."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter, description=__doc__
    )
    user_group = parser.add_mutually_exclusive_group(required=True)
    user_group.add_argument(
        "--all", action="store_true", help="Get email addresses of all users."
    )
    user_group.add_argument(
        "--lecture-owners",
        action="store_true",
        help="Get email addresses of users who own lecture.",
    )
    user_group.add_argument(
        "--lecturers",
        action="store_true",
        help="Get email addresses of users with 'lecturer' permission.",
    )
    parser.add_argument(
        "--db-url",
        help=(
            "Database URL to use instead of the one configured in rxconfig.py"
            " (e.g. 'sqlite:///reflex_main.db')."
        ),
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output."
    )
    return parser.parse_args()


def main() -> int:
    """Main function."""
    args = parse_args()

    try:
        _session = connect_database(db_url_override=args.db_url, read_only=True)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1

    from aitutor.models import (
        GlobalPermission,
        LectureRole,
        LinkUserLecture,
        LocalUser,
        Permission,
        UserInfo,
    )

    with _session() as session:
        stmt = select(UserInfo.email)

        if args.lecture_owners:
            stmt = (
                stmt.join(LocalUser)
                .join(LinkUserLecture)
                .where(LinkUserLecture.role == LectureRole.OWNER)
            )
        elif args.lecturers:
            stmt = (
                stmt.join(LocalUser)
                .join(Permission)
                .where(Permission.permission == GlobalPermission.LECTURER)
            )

        for email in session.exec(stmt.distinct()).all():
            print(email)

    return 0


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        sys.exit(main())
