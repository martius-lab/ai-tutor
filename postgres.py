#!/usr/bin/env python3
"""Script to manage the dockerized postgres database."""

import argparse
import pathlib
import sys
from subprocess import check_call

basedir = pathlib.Path(__file__).absolute().parent.name
DEFAULT_CONTAINER_ID = f"{basedir}-dev-db-1"

DB_NAME = "postgres"
DB_USER = "postgres"


def clear(container_id):
    """Clear the database, losing all existing data."""
    key = input(
        "Do you really want to clear the database?  Existing data will be lost! [yN] "
    )
    if key.lower() != "y":
        sys.exit(1)

    # clear existing database
    print("drop and re-create database")
    check_call(
        ["docker", "exec", "-it", container_id, "dropdb", DB_NAME, "-U", DB_USER]
    )
    check_call(
        ["docker", "exec", "-it", container_id, "createdb", DB_NAME, "-U", DB_USER]
    )


def restore(container_id, sqlfile):
    """Clear database and restore from the given SQL file."""
    if not sqlfile.is_file():
        raise RuntimeError(f"{sqlfile} is not a file.")

    key = input(
        "Do you really want to restore the database?  Existing data will be lost! [yN] "
    )
    if key.lower() != "y":
        sys.exit(1)

    # clear existing database
    print("drop and re-create database")
    check_call(
        ["docker", "exec", "-it", container_id, "dropdb", DB_NAME, "-U", DB_USER]
    )
    check_call(
        ["docker", "exec", "-it", container_id, "createdb", DB_NAME, "-U", DB_USER]
    )

    # load the dump
    print(f"load dump from {sqlfile}")
    check_call(["docker", "cp", str(sqlfile), f"{container_id}:/tmp/foo.sql"])
    check_call(
        [
            "docker",
            "exec",
            "-it",
            container_id,
            "psql",
            DB_NAME,
            DB_USER,
            "-f",
            "/tmp/foo.sql",
        ]
    )


def dump(container_id, outfile):
    """Dump the database to the given SQL file."""
    with open(outfile, "w") as f:
        check_call(
            [
                "docker",
                "exec",
                container_id,
                "pg_dump",
                "-U",
                DB_USER,
                "-h",
                "localhost",
                DB_NAME,
            ],
            stdout=f,
        )


def psql(container_id):
    """Run interactive postgres terminal."""
    check_call(["docker", "exec", "-it", container_id, "psql", DB_NAME, DB_USER])


def parse_args():
    """Parse command line arguments."""
    ap = argparse.ArgumentParser(description="Manage a dockerized PostgreSQL database.")
    ap.add_argument(
        "--container",
        "-c",
        type=str,
        default=DEFAULT_CONTAINER_ID,
        help="Name of the Docker container.  Default: '%(default)s'",
    )

    subparsers = ap.add_subparsers(
        help="Command (run '%(prog)s <cmd> -h' for more help).",
        dest="cmd",
        required=True,
    )

    parser_restore = subparsers.add_parser(
        "restore",
        help="Clear the existing database and restore it from the given SQL dump.",
    )
    parser_restore.add_argument(
        "-f",
        metavar="<file>",
        help="Path to the SQL file for restoring the database",
        type=pathlib.Path,
        required=True,
    )

    parser_dump = subparsers.add_parser(
        "dump",
        help="Dump the existing database to a SQL file.",
    )
    parser_dump.add_argument(
        "-o",
        metavar="<file>",
        help="Path to the output file",
        type=pathlib.Path,
        required=True,
    )

    _parser_clear = subparsers.add_parser(
        "clear",
        help="Clear the database.",
    )

    _parser_psql = subparsers.add_parser(
        "psql",
        help="Run interactive postgres terminal.",
    )

    return ap.parse_args()


def main() -> None:
    """Main function."""
    args = parse_args()

    match args.cmd:
        case "restore":
            restore(args.container, args.f)
        case "dump":
            dump(args.container, args.o)
        case "clear":
            clear(args.container)
        case "psql":
            psql(args.container)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
