"""
Database testing using pytest. To run test type 'pytest aitutor/tests/test_models.py'
in CLI.
"""

import reflex as rx
import pytest
from aitutor.models import User, Exercise, ExerciseResult


@pytest.fixture
def test_db():
    """
    Config for test database.
    """
    # Configure test database
    test_config = rx.Config(app_name="testing_app", db_url="sqlite:///test.db")
    yield test_config


"""

def test_exercise(test_db):

    with rx.session() as session:
        exercise_gradient = Exercise(
            title="Gradients",
            prompt="Please explain what a gradient is!",
            tags=["Gradient", "Derivative"],
        )
        session.add(exercise_gradient)
        exercise_gradientDescent = Exercise(
            title="Gradient Descent",
            prompt="Please explain how gradient descent works!",
            tags=["Gradient", "Derivative", "Algorithm"],
        )
        session.add(exercise_gradientDescent)
        list_exercises = session.exec(Exercise.select()).all()
        assert list_exercises == [exercise_gradient, exercise_gradientDescent]
        session.rollback()


def test_exerciseResult_relationships(test_db):

    with rx.session() as session:
        test_user_a = User(
            email="jane.doe@aitutor.com",
            password_hash="secure_password",
            enabled=True,
            role="student",
        )
        test_user_b = User(
            email="john.doe@aitutor.com",
            password_hash="secure_password",
            enabled=True,
            role="student",
        )
        exercise_gradient = Exercise(
            title="Gradient",
            prompt="Please explain what a gradient is!",
            tags=["Gradient", "Derivative"],
        )
        exercise_gradientDescent = Exercise(
            title="Gradient Descent",
            prompt="Please explain how gradient descent works!",
            tags=["Gradient", "Derivative", "Algorithm"],
        )
        user_a_submission_exercise_gradient = ExerciseResult(
            conversation_text=[  # type: ignore
                {
                    "role": "developer",
                    "content": "Please explain what a gradient is!",
                },
                {
                    "role": "user",
                    "content": "The gradient is the derivative of a scalar function!",
                },
            ],
            exercise=exercise_gradient,
            user=test_user_a,
        )
        user_b_submission_exercise_gradient = ExerciseResult(
            conversation_text=[  # type: ignore
                {
                    "role": "developer",
                    "content": "Please explain what a gradient is!",
                },
                {
                    "role": "user",
                    "content": "I don't know!",
                },
            ],
            exercise=exercise_gradient,
            user=test_user_b,
        )
        user_a_submission_exercise_gradientDescent = ExerciseResult(
            conversation_text=[  # type: ignore
                {
                    "role": "developer",
                    "content": "Please explain how gradient descent works!",
                },
                {
                    "role": "user",
                    "content": "GD calculates the gradients w.r.t. to the weights!",
                },
            ],
            exercise=exercise_gradientDescent,
            user=test_user_a,
        )
        user_b_submission_exercise_gradientDescent = ExerciseResult(
            conversation_text=[  # type: ignore
                {
                    "role": "developer",
                    "content": "Please explain how gradient descent works!",
                },
                {
                    "role": "user",
                    "content": "I don't know!",
                },
            ],
            exercise=exercise_gradientDescent,
            user=test_user_b,
        )
        session.add(test_user_a)
        session.add(test_user_b)
        session.add(exercise_gradient)
        session.add(exercise_gradientDescent)
        session.add(user_b_submission_exercise_gradient)
        session.add(user_a_submission_exercise_gradient)
        session.add(user_a_submission_exercise_gradientDescent)
        session.add(user_b_submission_exercise_gradientDescent)
        exercise = session.exec(
            Exercise.select().where(Exercise.title == "Gradient")
        ).one()
        assert exercise.submissions == [
            user_a_submission_exercise_gradient,
            user_b_submission_exercise_gradient,
        ]
        session.rollback()
"""
