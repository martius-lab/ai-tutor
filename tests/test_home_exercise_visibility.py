from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.dialects import sqlite

from aitutor.pages.home.state import build_home_exercises_statement


def compiled_sql(*, is_global_admin: bool) -> tuple[str, Mapping[str, Any]]:
    statement = build_home_exercises_statement(
        userinfo_id=17,
        user_id=23,
        is_global_admin=is_global_admin,
        now=datetime.now(UTC) + timedelta(days=1),
    )
    compiled = statement.compile(dialect=sqlite.dialect())
    return str(compiled), compiled.params


def test_regular_user_home_query_requires_lecture_membership():
    sql, params = compiled_sql(is_global_admin=False)

    assert "JOIN linkuserlecture" in sql
    assert "linkuserlecture.lecture_id = lecture.id" in sql
    assert "linkuserlecture.user_id = ?" in sql
    assert 23 in params.values()


def test_global_admin_home_query_does_not_require_lecture_membership():
    sql, _ = compiled_sql(is_global_admin=True)

    assert "JOIN linkuserlecture" not in sql


def test_home_query_only_joins_results_for_current_user():
    sql, params = compiled_sql(is_global_admin=False)

    assert (
        "exerciseresult.exercise_id = exercise.id" in sql
        or "exercise.id = exerciseresult.exercise_id" in sql
    )
    assert "exerciseresult.userinfo_id = ?" in sql
    assert 17 in params.values()


def test_home_query_excludes_expired_exercises_but_keeps_no_deadline():
    sql, _ = compiled_sql(is_global_admin=False)

    assert "exercise.deadline IS NULL OR exercise.deadline > ?" in sql