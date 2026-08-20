#!/usr/bin/env xonsh
# Script to restore the dockerized postgres database from some SQL dump

import argparse
import pathlib
import sys


DEFAULT_CONTAINER_ID = "ai-tutor-db-1"


def restore(container_id, sqlfile):
    if not sqlfile.is_file():
        raise RuntimeError(f"{sqlfile} is not a file.")

    key = input("Do you really want to restore the database?  Existing data will be lost! [yN] ")
    if key.lower() != "y":
        sys.exit(1)


    # clear existing database
    print("drop and re-create database")
    docker exec -it @(container_id) dropdb postgres -U postgres
    docker exec -it @(container_id) createdb postgres -U postgres

    # load the dump
    print(f"load dump from {sqlfile}")
    docker cp @(sqlfile) @(container_id):/tmp/foo.sql
    docker exec -it @(container_id) psql postgres postgres -f /tmp/foo.sql


def dump(container_id, outfile):
    docker exec @(container_id) pg_dump -U postgres -h localhost postgres > @(outfile)


def psql(container_id):
    docker exec -it @(container_id) psql postgres postgres


# create the top-level parser
ap = argparse.ArgumentParser(description="TODO")
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

# create the parser for the "a" command
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

# create the parser for the "b" command
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

parser_pqsl = subparsers.add_parser(
    "psql",
    help="Run interactive postgres terminal.",
)

args = ap.parse_args()


match args.cmd:
    case "restore":
        restore(args.container, args.f)
    case "dump":
        dump(args.container, args.o)
    case "psql":
        psql(args.container)
