"""Tests for the shared search query builder (aitutor/search/query.py)."""

import pytest
from sqlalchemy import (
    Column,
    ColumnElement,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    insert,
    select,
)

from aitutor.search.parser import FREE_TEXT_KEY, SearchTerm, parse_query_keys
from aitutor.search.query import SearchFields, any_of, build_search_condition

# A tiny stand-alone table, so these tests don't depend on the app's models.
metadata = MetaData()
items = Table(
    "items",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String),
    Column("author", String),
)

ROWS = {
    1: ("For Loops", "ana"),
    2: ("While Loops", "bob"),
    3: ("Recursion", "ana"),
    4: ("Lists", "chris"),
}


def title(value: str) -> ColumnElement[bool]:
    return items.c.title.ilike(f"%{value}%")


def author(value: str) -> ColumnElement[bool]:
    return items.c.author.ilike(f"%{value}%")


FIELDS: SearchFields = {
    "title": title,
    "author": author,
    FREE_TEXT_KEY: any_of(title, author),
}


@pytest.fixture(scope="module")
def conn():
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(
            insert(items),
            [{"id": i, "title": t, "author": a} for i, (t, a) in ROWS.items()],
        )
    with engine.connect() as connection:
        yield connection


def matching_ids(conn, terms) -> set[int]:
    condition = build_search_condition(terms, FIELDS)
    return set(conn.scalars(select(items.c.id).where(condition)))


# --- build_search_condition ---------------------------------------------------


def test_no_terms_matches_everything(conn):
    assert matching_ids(conn, []) == set(ROWS)


def test_single_term_uses_the_field_of_its_key(conn):
    assert matching_ids(conn, [SearchTerm("author", "ana")]) == {1, 3}


def test_terms_are_combined_with_and(conn):
    terms = [SearchTerm("author", "ana"), SearchTerm("title", "loops")]
    assert matching_ids(conn, terms) == {1}


def test_contradicting_terms_match_nothing(conn):
    terms = [SearchTerm("author", "ana"), SearchTerm("author", "bob")]
    assert matching_ids(conn, terms) == set()


def test_key_without_field_raises_key_error():
    with pytest.raises(KeyError):
        build_search_condition([SearchTerm("tag", "x")], FIELDS)


def test_accepts_any_iterable_of_terms(conn):
    terms = (t for t in [SearchTerm("title", "rec")])  # a generator, not a list
    assert matching_ids(conn, terms) == {3}


# --- any_of -------------------------------------------------------------------


def test_any_of_matches_if_any_field_matches(conn):
    # "ana" is an author, "loops" is a title: free text finds both
    assert matching_ids(conn, [SearchTerm(FREE_TEXT_KEY, "ana")]) == {1, 3}
    assert matching_ids(conn, [SearchTerm(FREE_TEXT_KEY, "loops")]) == {1, 2}


def test_any_of_single_field_behaves_like_the_field(conn):
    fields: SearchFields = {FREE_TEXT_KEY: any_of(title)}
    condition = build_search_condition([SearchTerm(FREE_TEXT_KEY, "lists")], fields)
    assert set(conn.scalars(select(items.c.id).where(condition))) == {4}


# --- parser + builder together -------------------------------------------------


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("", {1, 2, 3, 4}),
        ("author:ana", {1, 3}),
        ("AUTHOR:ANA", {1, 3}),  # keys and values are case-insensitive
        ('title:"for loops"', {1}),  # quoted value with a space
        ("loops author:bob", {2}),  # free text AND key
        ("ana loops", {1}),  # two free-text terms are ANDed
        ("unknown:ana", set()),  # unknown key becomes free text "unknown:ana"
        ("nothing", set()),
    ],
)
def test_parsed_query(conn, query, expected):
    terms = parse_query_keys(query, ["title", "author"])
    assert matching_ids(conn, terms) == expected
