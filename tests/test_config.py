from aitutor.config import get_exercises_json_schema


def test_get_exercises_json_schema():
    """Test the get_exercise_json_schema function."""
    schema = get_exercises_json_schema()

    assert isinstance(schema, dict)
    assert "title" in schema
    assert schema["title"] == "Exercises"

    path = ["properties", "exercises", "items", "properties", "lesson_context"]
    node = schema
    for i, key in enumerate(path):
        assert key in node, f"Key '{'.'.join(path[:i])}' not found in schema"
        node = node[key]

    assert "maxLength" in node
    assert node["maxLength"] == 100_000
