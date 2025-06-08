"""Module defining database models."""

from enum import IntEnum
import reflex as rx
from sqlmodel import Field, Column, JSON, Relationship, DateTime
from typing import Any, Dict, Optional, List
from datetime import datetime


class Tag(rx.Model, table=True):  # type: ignore
    """Tag model for storing allowed tags."""

    id: Optional[int] = Field(default=None, primary_key=True)  # Automatische ID
    name: str = Field(unique=True, nullable=False, index=True)  # Tag-Name, einzigartig

    def __repr__(self):
        return f"<Tag(name='{self.name}')>"


class Exercise(rx.Model, table=True):  # type: ignore
    """Exercise model for storing exercises."""

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(nullable=False)
    description: Optional[str] = Field(default=None)
    lesson_context: str = Field(default=None)
    prompt_name: str = Field(nullable=False, default="")
    prompt: str = Field(nullable=False, default="")
    tags: List[str] = Field(
        sa_column=Column(JSON), default=[]
    )  # Liste der Tags als JSON
    image: Optional[str] = Field(default=None)

    # Connects to ExerciseResult.exercise
    submissions: List["ExerciseResult"] = Relationship(
        back_populates="exercise", cascade_delete=True
    )

    def __repr__(self):
        return f"<Exercise(id={self.id}, title='{self.title}')>"


class ExerciseResult(rx.Model, table=True):  # type: ignore
    """
    ExerciseResult model for storing conversation and result of an exercise and a user.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_text: List[Dict[str, Any]] = Field(sa_column=Column(JSON), default=[])
    check_passed: bool = Field(default=False)
    finished_conversation: List[Dict[str, Any]] = Field(
        sa_column=Column(JSON), default=[]
    )
    submit_time_stamp: Optional[datetime] = Field(
        sa_column=Column(
            type_=DateTime(timezone=True),
        )
    )

    # Connects to Exercise.submissions
    exercise_id: int = Field(foreign_key="exercise.id", ondelete="CASCADE")
    exercise: "Exercise" = Relationship(back_populates="submissions")

    userinfo_id: int = Field(foreign_key="userinfo.id", ondelete="CASCADE")
    user: "UserInfo" = Relationship(back_populates="exercise_results")

    def __repr__(self):
        return (
            f"<ExerciseResult(exercise_title={self.exercise.title}, "
            f"exercise_id={self.exercise_id}, "
            f"user_id={self.userinfo_id})>"
        )


class UserRole(IntEnum):
    """
    Enum for user roles.
    """

    STUDENT = 1
    TEACHER = 2
    ADMIN = 3


class UserInfo(rx.Model, table=True):
    """
    Adds more attributes to a user than just name and password.
    """

    email: str
    role: UserRole
    user_id: int = Field(foreign_key="localuser.id", ondelete="CASCADE")
    exercise_results: List["ExerciseResult"] = Relationship(
        back_populates="user", cascade_delete=True
    )
