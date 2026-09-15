#!/usr/bin/env python3
"""Set the password of an AI Tutor user.

The database connection is taken from the Reflex configuration in ``rxconfig.py``
(overridable with ``--db-url`` or the ``REFLEX_DB_URL`` environment variable), so
the script must be run from the project root:

    uv run ./scripts/set_user_password.py alice
    uv run ./scripts/set_user_password.py --email alice@example.com --revoke-sessions
    uv run ./scripts/set_user_password.py alice --password-stdin < password.txt
    uv run ./scripts/set_user_password.py --list

Without ``--password-stdin`` the new password is asked for interactively (twice).
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys


def parse_args() -> argparse.Namespace:
    """Parse the command line arguments."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
    )
    user_group = parser.add_mutually_exclusive_group(required=False)
    user_group.add_argument(
        "--name",
        dest="username",
        help="Name of the user whose password is changed.",
    )
    user_group.add_argument(
        "--email",
        help="Select the user by email address instead of by username.",
    )
    parser.add_argument(
        "--password-stdin",
        action="store_true",
        help=(
            "Read the new password from stdin (first line) instead of asking for"
            " it interactively."
        ),
    )
    parser.add_argument(
        "--revoke-sessions",
        action="store_true",
        help="Also log the user out everywhere by deleting their auth sessions.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Only list the users in the database and exit.",
    )
    parser.add_argument(
        "--db-url",
        help=(
            "Database URL to use instead of the one configured in rxconfig.py"
            " (e.g. 'sqlite:///reflex_main.db')."
        ),
    )
    args = parser.parse_args()

    if not args.list and bool(args.username) == bool(args.email):
        parser.error("Provide either a --name or --email (but not both).")

    return args


def prompt_password(max_bytes: int) -> str:
    """Ask the user for the new password twice and return it.

    Args:
        max_bytes: Maximum allowed length of the password in bytes.

    Returns:
        The new password.

    Raises:
        SystemExit: If the two entered passwords do not match.
    """
    password = getpass.getpass("New password: ")
    confirmation = getpass.getpass("Repeat new password: ")

    if password != confirmation:
        sys.exit("Error: The entered passwords do not match.")

    check_password(password, max_bytes)
    return password


def check_password(password: str, max_bytes: int) -> None:
    """Validate the given password.

    Args:
        password: The password to check.
        max_bytes: Maximum allowed length of the password in bytes.

    Raises:
        SystemExit: If the password is empty or too long.
    """
    if not password:
        sys.exit("Error: The password must not be empty.")

    # bcrypt (and thus the login form of the app) only supports a limited length
    if len(password.encode("utf-8")) > max_bytes:
        sys.exit(f"Error: The password must not be longer than {max_bytes} bytes.")


def user_query():
    """Build a select for all users together with their user info.

    Returns:
        A SQLModel select statement yielding ``(LocalUser, UserInfo | None)`` rows.
    """
    from reflex_local_auth.user import LocalUser
    from sqlmodel import select

    from aitutor.models import UserInfo

    return select(LocalUser, UserInfo).join(UserInfo)


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
    from reflex_local_auth.auth_session import LocalAuthSession
    from reflex_local_auth.user import LocalUser
    from sqlmodel import select

    from aitutor import global_vars as gv
    from aitutor.models import UserInfo

    with rx.session() as session:
        url = session.get_bind().engine.url
        print(f"Database: {url.render_as_string(hide_password=True)}")

        if args.list:
            users = session.exec(user_query()).all()
            for local_user, user_info in users:
                status = "enabled" if local_user.enabled else "disabled"
                email = user_info.email if user_info else "<no user info>"
                print(f"{local_user.id}\t{local_user.username}\t{email}\t{status}")
            return 0

        query = user_query()
        if args.username:
            query = query.where(LocalUser.username == args.username)
            identifier = f"username '{args.username}'"
        else:
            query = query.where(UserInfo.email == args.email)
            identifier = f"email '{args.email}'"

        matches = session.exec(query).all()
        if not matches:
            sys.exit(f"Error: No user found with {identifier}.")
        if len(matches) > 1:
            sys.exit(
                f"Error: Found {len(matches)} users with {identifier}."
                " Please select the user by username."
            )

        local_user, user_info = matches[0]
        assert local_user.id is not None
        email = user_info.email if user_info else "<no user info>"
        print(
            f"Setting password of user '{local_user.username}'"
            f" (id={local_user.id}, email={email})."
        )

        if args.password_stdin:
            password = sys.stdin.readline().rstrip("\n")
            check_password(password, gv.PASSWORD_MAX_BYTES)
        else:
            password = prompt_password(gv.PASSWORD_MAX_BYTES)

        local_user.password_hash = LocalUser.hash_password(password)
        session.add(local_user)

        if args.revoke_sessions:
            auth_sessions = session.exec(
                select(LocalAuthSession).where(
                    LocalAuthSession.user_id == local_user.id
                )
            ).all()
            for auth_session in auth_sessions:
                session.delete(auth_session)
            print(f"Revoked {len(auth_sessions)} active login session(s).")

        session.commit()

    print("Password updated successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
