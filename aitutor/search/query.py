"""Build the SQL condition for a search query.

Each page maps its search keys to fields; this module combines them::

    fields = {
        SearchKey.TITLE: title,                               # title:loop
        SearchKey.FREE_TEXT: any_of(title, description, tag), # loop
    }
    stmt.where(build_search_condition(terms, fields))
"""

from collections.abc import Callable, Iterable, Mapping

from sqlalchemy import ColumnElement, and_, or_, true
from sqlmodel import col

from aitutor.search.parser import SearchTerm

#: One searchable column of a page: turns the typed value into a SQL condition.
#: Example: `title("loop")` -> `exercise.title ILIKE '%loop%'`.
SearchField = Callable[[str], ColumnElement[bool]]

#: A page's search key -> field mapping, e.g. `{SearchKey.TITLE: title}`.
SearchFields = Mapping[str, SearchField]


def contains(column: object) -> SearchField:
    """Field that matches if `column` contains the value (case-insensitive).

    Example: `contains(Exercise.title)("loop")` -> `exercise.title ILIKE '%loop%'`.
    """

    def match(value: str) -> ColumnElement[bool]:
        return col(column).ilike(f"%{value}%")

    return match


def any_contains(relationship: object, column: object) -> SearchField:
    """Field that matches if any related row's `column` contains the value.

    Example: `any_contains(Exercise.tags, Tag.name)("py")` -> exercise has a tag
    whose name contains "py".
    """

    def match(value: str) -> ColumnElement[bool]:
        return col(relationship).any(contains(column)(value))

    return match


def any_of(*fields: SearchField) -> SearchField:
    """Combine fields into one that matches if any of them matches.

    Example: `any_of(title, tag)("loop")` -> `title(...) OR tag(...)`.
    """

    def match_any(value: str) -> ColumnElement[bool]:
        return or_(*(field(value) for field in fields))

    return match_any


def build_search_condition(
    terms: Iterable[SearchTerm], fields: SearchFields
) -> ColumnElement[bool]:
    """Combine the search terms with AND, using the field of each term's key.

    Example: `loop tag:python` -> `fields["rest"]("loop") AND fields["tag"]("python")`.
    Without terms, the condition matches everything.
    """
    conditions = [fields[term.key](term.value) for term in terms]
    if not conditions:
        return true()
    return and_(*conditions)
