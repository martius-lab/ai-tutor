import json
import re

import pytest
import reflex as rx
from sqlalchemy.orm import selectinload
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from aitutor.models import Exercise, Lecture, Prompt, Tag
from aitutor.pages.lecture_manage_exercises.state import _import_exercises


@pytest.fixture
def engine(monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    monkeypatch.setattr(rx, "session", lambda: Session(engine))
    return engine


@pytest.fixture
def lecture_id(engine) -> int:
    with Session(engine) as session:
        lecture = Lecture(lecture_name="Lecture")
        session.add(lecture)
        session.commit()
        assert lecture.id is not None
        return lecture.id


@pytest.fixture
def other_lecture_id(engine, lecture_id) -> int:
    with Session(engine) as session:
        other = Lecture(lecture_name="Other lecture")
        session.add(other)
        session.commit()
        assert other.id is not None
        return other.id


def make_exercise(**overrides) -> dict:
    exercise = {
        "title": "Exercise 1",
        "description": "Solve it.",
        "lesson_context": "Some context.",
        "prompt_name": "My prompt",
        "is_hidden": False,
        "deadline": None,
        "days_to_complete": None,
        "tags": [],
    }
    exercise.update(overrides)
    return exercise


def all_rows(engine, model):
    with Session(engine) as session:
        return list(session.exec(select(model)).all())


def lecture_exercises(engine, lecture_id) -> list[Exercise]:
    with Session(engine) as session:
        return list(
            session.exec(
                select(Exercise)
                .where(Exercise.lecture_id == lecture_id)
                .options(
                    selectinload(Exercise.tags),  # type: ignore
                    selectinload(Exercise.prompt),  # type: ignore
                )
                .order_by(Exercise.id)  # type: ignore
            ).all()
        )


def add_prompt(engine, name: str, template: str, lecture_id: int | None) -> int:
    with Session(engine) as session:
        prompt = Prompt(name=name, prompt_template=template, lecture_id=lecture_id)
        session.add(prompt)
        session.commit()
        assert prompt.id is not None
        return prompt.id


def set_default_prompt(engine, lecture_id: int, prompt_id: int):
    with Session(engine) as session:
        lecture = session.get(Lecture, lecture_id)
        assert lecture is not None
        lecture.default_prompt_id = prompt_id
        session.add(lecture)
        session.commit()


def exercise_without_prompt_name(how: str, **overrides) -> dict:
    exercise = make_exercise(**overrides)
    if how == "omitted":
        del exercise["prompt_name"]
    else:
        exercise["prompt_name"] = ""
    return exercise


# --- Successful imports ---


def test_import_creates_exercise_prompt_and_tags(engine, lecture_id):
    data = {
        "prompt_templates": {"My prompt": "Template text"},
        "exercises": [
            make_exercise(
                title="Recursion",
                description="Explain recursion.",
                lesson_context="Lesson about recursion.",
                is_hidden=True,
                deadline="2026-10-01T12:30:00",
                days_to_complete=7,
                tags=["week 1", "recursion"],
            )
        ],
    }

    assert _import_exercises(lecture_id, json.dumps(data).encode()) == (
        1,
        ["My prompt"],
        [],
    )

    [exercise] = lecture_exercises(engine, lecture_id)
    assert exercise.title == "Recursion"
    assert exercise.description == "Explain recursion."
    assert exercise.lesson_context == "Lesson about recursion."
    assert exercise.is_hidden is True
    assert exercise.deadline is not None
    assert exercise.deadline.isoformat() == "2026-10-01T12:30:00"
    assert exercise.days_to_complete == 7
    assert sorted(tag.name for tag in exercise.tags) == ["recursion", "week 1"]
    assert exercise.prompt is not None
    assert exercise.prompt.name == "My prompt"
    assert exercise.prompt.prompt_template == "Template text"
    assert exercise.prompt.lecture_id == lecture_id

    tags = all_rows(engine, Tag)
    assert all(tag.lecture_id == lecture_id for tag in tags)


def test_import_multiple_exercises(engine, lecture_id):
    data = {
        "prompt_templates": {"A": "Template A", "B": "Template B"},
        "exercises": [
            make_exercise(title="Ex 1", prompt_name="A"),
            make_exercise(title="Ex 2", prompt_name="B"),
            make_exercise(title="Ex 3", prompt_name="A"),
        ],
    }

    assert _import_exercises(lecture_id, json.dumps(data).encode()) == (
        3,
        ["A", "B"],
        [],
    )

    exercises = lecture_exercises(engine, lecture_id)
    assert [(e.title, e.prompt.name) for e in exercises] == [  # type: ignore
        ("Ex 1", "A"),
        ("Ex 2", "B"),
        ("Ex 3", "A"),
    ]
    assert len(all_rows(engine, Prompt)) == 2


def test_import_without_tags_field(engine, lecture_id):
    exercise = make_exercise()
    del exercise["tags"]

    _import_exercises(
        lecture_id,
        json.dumps(
            {"prompt_templates": {"My prompt": "t"}, "exercises": [exercise]}
        ).encode(),
    )

    [imported] = lecture_exercises(engine, lecture_id)
    assert imported.tags == []


def test_import_empty_exercise_list(engine, lecture_id):
    assert _import_exercises(lecture_id, json.dumps({"exercises": []}).encode()) == (
        0,
        [],
        [],
    )
    assert all_rows(engine, Exercise) == []


# --- Prompt conflict handling ---


def test_existing_lecture_prompt_with_same_content_is_reused(engine, lecture_id):
    prompt_id = add_prompt(engine, "My prompt", "Same template", lecture_id)

    result = _import_exercises(
        lecture_id,
        json.dumps(
            {
                "prompt_templates": {"My prompt": "Same template"},
                "exercises": [make_exercise()],
            }
        ).encode(),
    )

    assert result == (1, [], [])
    assert len(all_rows(engine, Prompt)) == 1
    [exercise] = lecture_exercises(engine, lecture_id)
    assert exercise.prompt_id == prompt_id


def test_existing_global_prompt_with_same_content_is_reused(engine, lecture_id):
    prompt_id = add_prompt(engine, "My prompt", "Same template", None)

    result = _import_exercises(
        lecture_id,
        json.dumps(
            {
                "prompt_templates": {"My prompt": "Same template"},
                "exercises": [make_exercise()],
            }
        ).encode(),
    )

    assert result == (1, [], [])
    assert len(all_rows(engine, Prompt)) == 1
    [exercise] = lecture_exercises(engine, lecture_id)
    assert exercise.prompt_id == prompt_id


def test_prompt_with_same_name_but_different_content_is_renamed(engine, lecture_id):
    existing_id = add_prompt(engine, "My prompt", "Old template", lecture_id)

    result = _import_exercises(
        lecture_id,
        json.dumps(
            {
                "prompt_templates": {"My prompt": "New template"},
                "exercises": [make_exercise()],
            }
        ).encode(),
    )

    assert result == (1, [], [("My prompt", "My prompt (imported 1)")])

    # Check that the existing prompt was not modified
    with Session(engine) as session:
        existing = session.get(Prompt, existing_id)
        assert existing is not None
        assert existing.prompt_template == "Old template"

    [exercise] = lecture_exercises(engine, lecture_id)
    assert exercise.prompt_id != existing_id
    assert exercise.prompt is not None
    assert exercise.prompt.name == "My prompt (imported 1)"


def test_conflicting_global_prompt_causes_rename(engine, lecture_id):
    add_prompt(engine, "My prompt", "Global template", None)

    _import_exercises(
        lecture_id,
        json.dumps(
            {
                "prompt_templates": {"My prompt": "New template"},
                "exercises": [make_exercise()],
            }
        ).encode(),
    )

    [exercise] = lecture_exercises(engine, lecture_id)
    assert exercise.prompt is not None
    assert exercise.prompt.name == "My prompt (imported 1)"


def test_prompt_rename_counter_skips_taken_names(engine, lecture_id):
    add_prompt(engine, "My prompt", "v1", lecture_id)
    add_prompt(engine, "My prompt (imported 1)", "v2", lecture_id)

    _, _, renames = _import_exercises(
        lecture_id,
        json.dumps(
            {
                "prompt_templates": {"My prompt": "v3"},
                "exercises": [make_exercise()],
            }
        ).encode(),
    )

    assert renames == [("My prompt", "My prompt (imported 2)")]
    [exercise] = lecture_exercises(engine, lecture_id)
    assert exercise.prompt is not None
    assert exercise.prompt.name == "My prompt (imported 2)"
    assert exercise.prompt.prompt_template == "v3"


def test_prompt_of_other_lecture_does_not_conflict(
    engine, lecture_id, other_lecture_id
):
    other_id = add_prompt(engine, "My prompt", "Other template", other_lecture_id)

    result = _import_exercises(
        lecture_id,
        json.dumps(
            {
                "prompt_templates": {"My prompt": "Other template"},
                "exercises": [make_exercise()],
            }
        ).encode(),
    )

    assert result == (1, ["My prompt"], [])
    [exercise] = lecture_exercises(engine, lecture_id)
    assert exercise.prompt is not None
    assert exercise.prompt.id != other_id
    assert exercise.prompt.name == "My prompt"
    assert exercise.prompt.lecture_id == lecture_id


# --- Missing prompt name falls back to the lecture's default prompt ---


@pytest.mark.parametrize("how", ["omitted", "empty"])
def test_missing_prompt_name_uses_lecture_default_prompt(engine, lecture_id, how):
    default_id = add_prompt(engine, "Default", "Default template", lecture_id)
    set_default_prompt(engine, lecture_id, default_id)

    result = _import_exercises(
        lecture_id,
        json.dumps({"exercises": [exercise_without_prompt_name(how)]}).encode(),
    )

    assert result == (1, [], [])
    assert len(all_rows(engine, Prompt)) == 1
    [exercise] = lecture_exercises(engine, lecture_id)
    assert exercise.prompt_id == default_id


@pytest.mark.parametrize("how", ["omitted", "empty"])
def test_missing_prompt_name_uses_global_default_prompt_of_lecture(
    engine, lecture_id, how
):
    default_id = add_prompt(engine, "Global", "Global template", None)
    set_default_prompt(engine, lecture_id, default_id)

    _import_exercises(
        lecture_id,
        json.dumps({"exercises": [exercise_without_prompt_name(how)]}).encode(),
    )

    [exercise] = lecture_exercises(engine, lecture_id)
    assert exercise.prompt_id == default_id


@pytest.mark.parametrize("how", ["omitted", "empty"])
def test_missing_prompt_name_uses_global_default_on_lecture_without_default(
    engine, lecture_id, how
):
    # Add both global and lecture-specific prompt but don't set a default for the
    # lecture
    add_prompt(engine, "Global", "Global template", None)
    add_prompt(engine, "Local", "Local template", None)

    with pytest.raises(RuntimeError, match="lecture has no default prompt"):
        _import_exercises(
            lecture_id,
            json.dumps(
                {
                    "prompt_templates": {"My prompt": "Imported template"},
                    "exercises": [
                        make_exercise(title="Named"),
                        exercise_without_prompt_name("omitted", title="Omitted"),
                        exercise_without_prompt_name("empty", title="Empty"),
                    ],
                }
            ).encode(),
        )

    # make sure nothing was imported
    assert all_rows(engine, Exercise) == []
    assert all_rows(engine, Tag) == []


def test_exercises_with_and_without_prompt_name_can_be_mixed(engine, lecture_id):
    default_id = add_prompt(engine, "Default", "Default template", lecture_id)
    set_default_prompt(engine, lecture_id, default_id)

    result = _import_exercises(
        lecture_id,
        json.dumps(
            {
                "prompt_templates": {"My prompt": "Imported template"},
                "exercises": [
                    make_exercise(title="Named"),
                    exercise_without_prompt_name("omitted", title="Omitted"),
                    exercise_without_prompt_name("empty", title="Empty"),
                ],
            }
        ).encode(),
    )

    assert result == (3, ["My prompt"], [])
    exercises = lecture_exercises(engine, lecture_id)
    assert [(e.title, e.prompt.name) for e in exercises] == [  # type: ignore
        ("Named", "My prompt"),
        ("Omitted", "Default"),
        ("Empty", "Default"),
    ]


# --- Title and tag handling ---


def test_duplicate_title_in_lecture_is_renamed(engine, lecture_id):
    data = {"prompt_templates": {"My prompt": "t"}, "exercises": [make_exercise()]}
    _import_exercises(lecture_id, json.dumps(data).encode())
    _import_exercises(lecture_id, json.dumps(data).encode())
    _import_exercises(lecture_id, json.dumps(data).encode())

    titles = [e.title for e in lecture_exercises(engine, lecture_id)]
    assert titles == [
        "Exercise 1",
        "Exercise 1 (imported 1)",
        "Exercise 1 (imported 2)",
    ]


def test_duplicate_titles_within_one_file_are_renamed(engine, lecture_id):
    data = {
        "prompt_templates": {"My prompt": "t"},
        "exercises": [make_exercise(), make_exercise()],
    }

    _import_exercises(lecture_id, json.dumps(data).encode())

    titles = [e.title for e in lecture_exercises(engine, lecture_id)]
    assert titles == ["Exercise 1", "Exercise 1 (imported 1)"]


def test_same_title_in_other_lecture_is_not_renamed(
    engine, lecture_id, other_lecture_id
):
    with Session(engine) as session:
        session.add(Exercise(title="Exercise 1", lecture_id=other_lecture_id))
        session.commit()

    _import_exercises(
        lecture_id,
        json.dumps(
            {"prompt_templates": {"My prompt": "t"}, "exercises": [make_exercise()]}
        ).encode(),
    )

    [exercise] = lecture_exercises(engine, lecture_id)
    assert exercise.title == "Exercise 1"


def test_existing_tags_are_reused(engine, lecture_id, other_lecture_id):
    with Session(engine) as session:
        session.add(Tag(name="existing", lecture_id=lecture_id))
        session.add(Tag(name="foreign", lecture_id=other_lecture_id))
        session.commit()

    data = {
        "prompt_templates": {"My prompt": "t"},
        "exercises": [
            make_exercise(title="A", tags=["existing", "foreign", "new"]),
            make_exercise(title="B", tags=["new"]),
        ],
    }

    _import_exercises(lecture_id, json.dumps(data).encode())

    with Session(engine) as session:
        lecture_tags = session.exec(
            select(Tag).where(Tag.lecture_id == lecture_id)
        ).all()
        assert sorted(t.name for t in lecture_tags) == ["existing", "foreign", "new"]
        other_tags = session.exec(
            select(Tag).where(Tag.lecture_id == other_lecture_id)
        ).all()
        assert [t.name for t in other_tags] == ["foreign"]

    a, b = lecture_exercises(engine, lecture_id)
    assert all(tag.lecture_id == lecture_id for tag in a.tags)
    assert {t.id for t in b.tags} <= {t.id for t in a.tags}


# --- Error handling ---


def assert_nothing_imported(engine):
    assert all_rows(engine, Exercise) == []
    assert all_rows(engine, Prompt) == []
    assert all_rows(engine, Tag) == []


def test_invalid_json_raises(engine, lecture_id):
    with pytest.raises(ValueError, match="Invalid JSON file."):
        _import_exercises(lecture_id, b"{not json")

    assert_nothing_imported(engine)


def test_non_utf8_file_raises(engine, lecture_id):
    with pytest.raises(UnicodeDecodeError):
        _import_exercises(lecture_id, b"\xff\xfe\x00")

    assert_nothing_imported(engine)


def test_missing_exercises_key_raises_schema_error(engine, lecture_id):
    with pytest.raises(
        ValueError,
        match="Invalid data format: document: 'exercises' is a required property",
    ):
        _import_exercises(
            lecture_id, json.dumps({"prompt_templates": {"My prompt": "t"}}).encode()
        )

    assert_nothing_imported(engine)


def test_missing_required_exercise_field_raises_schema_error(engine, lecture_id):
    exercise = make_exercise()
    del exercise["description"]

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Invalid data format: $.exercises[0]: 'description' is a required"
        ),
    ):
        _import_exercises(
            lecture_id,
            json.dumps(
                {"prompt_templates": {"My prompt": "t"}, "exercises": [exercise]}
            ).encode(),
        )

    assert_nothing_imported(engine)


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"title": ""}, "$.exercises[0].title violates constraint minLength=1."),
        ({"title": "x" * 501}, "$.exercises[0].title violates constraint maxLength"),
        ({"is_hidden": "yes"}, "$.exercises[0].is_hidden violates constraint type"),
        ({"days_to_complete": 0}, "days_to_complete violates constraint minimum=1."),
        ({"tags": ["a", "a"]}, "$.exercises[0].tags violates constraint uniqueItems"),
    ],
)
def test_schema_constraint_violations_raise(engine, lecture_id, overrides, expected):
    with pytest.raises(ValueError, match=re.escape(expected)):
        _import_exercises(
            lecture_id,
            json.dumps(
                {
                    "prompt_templates": {"My prompt": "t"},
                    "exercises": [make_exercise(**overrides)],
                }
            ).encode(),
        )

    assert_nothing_imported(engine)


def test_unknown_prompt_name_rolls_back_whole_import(engine, lecture_id):
    data = {
        "prompt_templates": {"My prompt": "t"},
        "exercises": [
            make_exercise(title="Valid", tags=["tag"]),
            make_exercise(title="Broken", prompt_name="Missing prompt"),
        ],
    }

    with pytest.raises(ValueError, match="Prompt 'Missing prompt' not found"):
        _import_exercises(lecture_id, json.dumps(data).encode())

    assert_nothing_imported(engine)


def test_prompt_templates_are_optional_but_prompt_must_resolve(engine, lecture_id):
    with pytest.raises(ValueError, match="Prompt 'My prompt' not found"):
        _import_exercises(
            lecture_id, json.dumps({"exercises": [make_exercise()]}).encode()
        )

    assert_nothing_imported(engine)


def test_invalid_deadline_raises(engine, lecture_id):
    with pytest.raises(ValueError):
        _import_exercises(
            lecture_id,
            json.dumps(
                {
                    "prompt_templates": {"My prompt": "t"},
                    "exercises": [make_exercise(deadline="not a date")],
                }
            ).encode(),
        )

    assert_nothing_imported(engine)
