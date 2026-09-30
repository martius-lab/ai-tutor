#!/usr/bin/env python3
"""Clean up email verification data of AI Tutor.

- Deletes accounts whose email address has not been confirmed within the configured
  period after their creation.
- Purges expired verification tokens.

Meant to be run regularly, e.g. once a day via cron.  The database connection is taken
from the Reflex configuration in ``rxconfig.py`` (overridable with ``--db-url`` or the
``REFLEX_DB_URL`` environment variable), so the script must be run from the project
root:

    uv run ./scripts/cleanup_accounts.py
    uv run ./scripts/cleanup_accounts.py --dry-run

In the docker setup (see docs/docker.md):

    docker compose -f compose.prod.yaml exec -T app python scripts/cleanup_accounts.py

The exit code is 0 on success, 1 on errors and 2 if there are accounts that are due for
deletion but have been kept and need to be looked at by an admin.  cron mails the output
by default, so ``--quiet`` only prints something if there is anything to report.
"""

from __future__ import annotations

import argparse
import os
import sys

EXIT_ATTENTION_NEEDED = 2


def parse_args() -> argparse.Namespace:
    """Parse the command line arguments."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only report what would be deleted, do not change the database.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print something if accounts are deleted or need attention.",
    )
    parser.add_argument(
        "--db-url",
        help=(
            "Database URL to use instead of the one configured in rxconfig.py"
            " (e.g. 'sqlite:///reflex_main.db')."
        ),
    )
    return parser.parse_args()


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

    from aitutor.account_cleanup import delete_unverified_accounts, purge_expired_tokens

    def info(message: str) -> None:
        if not args.quiet:
            print(message)

    prefix = "[dry run] " if args.dry_run else ""

    with rx.session() as session:
        url = session.get_bind().engine.url
        info(f"{prefix}Database: {url.render_as_string(hide_password=True)}")

        # Accounts first: their tokens are deleted with them.
        accounts = delete_unverified_accounts(session)
        num_tokens = purge_expired_tokens(session)

        if args.dry_run:
            session.rollback()
        else:
            session.commit()

    for account in accounts.deleted:
        print(
            f"{prefix}Deleted unverified account '{account.username}'"
            f" (id={account.user_id}, email={account.email},"
            f" created {account.created_at:%Y-%m-%d %H:%M})."
        )
    for account in accounts.skipped_sole_lecture_owner:
        print(
            f"{prefix}WARNING: Kept unverified account '{account.username}'"
            f" (id={account.user_id}, email={account.email},"
            f" created {account.created_at:%Y-%m-%d %H:%M}) because it is the only"
            " owner of a lecture.  Please check it in the user management."
        )
    info(
        f"{prefix}Deleted {len(accounts.deleted)} unverified account(s) and"
        f" {num_tokens} expired verification token(s)."
    )

    if accounts.skipped_sole_lecture_owner:
        return EXIT_ATTENTION_NEEDED
    return 0


if __name__ == "__main__":
    sys.exit(main())
