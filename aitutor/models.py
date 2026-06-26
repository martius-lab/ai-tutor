"""Module defining database models."""

from datetime import datetime, timedelta
from enum import IntEnum, StrEnum
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

import sqlalchemy as sa
from reflex_local_auth.user import LocalUser
from sqlalchemy import ForeignKey as SAForeignKey
from sqlmodel import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    Field,
    Relationship,
    SQLModel,
)

from aitutor.global_vars import TIME_ZONE


class Language(StrEnum):
    """
    Enum for supported languages.
    """

    DE = "de"
    EN = "en"


class UserRole(IntEnum):
    """
    Enum for user roles.
    """

    STUDENT = 1
    TUTOR = 2
    ADMIN = 3


class ExerciseTagLink(SQLModel, table=True):
    """
    Link table for many-to-many relationship between Exercise and Tag.
    """

    # database relationships
    exercise_id: Optional[int] = Field(
        foreign_key="exercise.id", primary_key=True, ondelete="CASCADE"
    )
    tag_id: Optional[int] = Field(
        foreign_key="tag.id", primary_key=True, ondelete="CASCADE"
    )


class Tag(SQLModel, table=True):
    """Tag model for storing allowed tags."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, nullable=False, index=True)

    # ORM relationship
    exercises: List["Exercise"] = Relationship(
        back_populates="tags", link_model=ExerciseTagLink
    )

    def __repr__(self):
        return f"<Tag(name='{self.name}')>"


class Exercise(SQLModel, table=True):
    """Exercise model for storing exercises."""

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(nullable=False, default="", unique=True)
    description: str = Field(nullable=False, default="")
    lesson_context: str = Field(nullable=False, default="")
    prompt_id: Optional[int] = Field(default=None, foreign_key="prompt.id")
    is_hidden: bool = Field(default=False)
    deadline: Optional[datetime] = Field(
        sa_column=Column(DateTime, nullable=True), default=None
    )
    days_to_complete: Optional[int] = Field(default=None)

    # ORM relationship
    submissions: List["ExerciseResult"] = Relationship(
        back_populates="exercise", sa_relationship_kwargs={"passive_deletes": True}
    )
    tags: List[Tag] = Relationship(
        back_populates="exercises", link_model=ExerciseTagLink
    )
    prompt: Optional["Prompt"] = Relationship()

    @property
    def editing_period(self) -> str:
        """
        Returns a string representing the editing period based on
        the deadline and days to complete.
        """
        if self.deadline and self.days_to_complete:
            start = self.deadline - timedelta(days=self.days_to_complete)
            return f"{start.strftime('%d.%m.%Y')} -\
                {self.deadline.strftime('%d.%m.%Y, %H:%M')}"
        else:
            return "No deadline"

    @property
    def is_started(self) -> bool:
        """
        flag wheter the exercise is started.
        It is used to show what exercise is automatically hidden
        """
        if self.deadline and self.days_to_complete:
            end = self.deadline.replace(tzinfo=ZoneInfo(TIME_ZONE))
            start = end - timedelta(days=self.days_to_complete)
            current_time = datetime.now(ZoneInfo(TIME_ZONE))
            return current_time > start
        # if no deadline is set, the exercise counts as started
        return True

    @property
    def deadline_exceeded(self) -> bool:
        """
        flag wheter the deadline of the exercise is over.
        """
        if self.deadline:
            deadline = self.deadline.replace(tzinfo=ZoneInfo(TIME_ZONE))
            return datetime.now(ZoneInfo(TIME_ZONE)) > deadline
        return False

    def __repr__(self):
        return f"<Exercise(id={self.id}, title='{self.title}')>"


class ExerciseResult(SQLModel, table=True):
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
        ),
        default=None,
    )
    tokens_used: int = Field(default=0)

    # database relationships
    exercise_id: int = Field(foreign_key="exercise.id", ondelete="CASCADE")
    userinfo_id: int = Field(foreign_key="userinfo.id", ondelete="CASCADE")

    # ORM relationships
    exercise: "Exercise" = Relationship(back_populates="submissions")
    user: "UserInfo" = Relationship(back_populates="exercise_results")

    def __repr__(self):
        return (
            f"<ExerciseResult(exercise_title={self.exercise.title}, "
            f"exercise_id={self.exercise_id}, "
            f"userinfo_id={self.userinfo_id})>"
        )


class BetaExercise(SQLModel, table=True):
    """
    Independent exercise model for the Beta AI Tutor workflow.

    Beta exercises intentionally do not reuse the regular Exercise/ExerciseResult
    tables. They are the author-facing container for generated and manually curated
    concepts, core points, and misconception hints.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(nullable=False, default="", unique=True)
    description: str = Field(nullable=False, default="")
    source_material_text: str = Field(nullable=False, default="")
    source_material_filename: str = Field(nullable=False, default="")
    is_hidden: bool = Field(default=False)
    deadline: Optional[datetime] = Field(
        sa_column=Column(DateTime, nullable=True), default=None
    )
    days_to_complete: Optional[int] = Field(default=None)

    # ORM relationships
    concepts: List["BetaConcept"] = Relationship(
        back_populates="beta_exercise", sa_relationship_kwargs={"passive_deletes": True}
    )

    @property
    def editing_period(self) -> str:
        """
        Returns a string representing the editing period based on
        the deadline and days to complete.
        """
        if self.deadline and self.days_to_complete:
            start = self.deadline - timedelta(days=self.days_to_complete)
            return f"{start.strftime('%d.%m.%Y')} -\
                {self.deadline.strftime('%d.%m.%Y, %H:%M')}"
        return "No deadline"

    @property
    def is_started(self) -> bool:
        """
        Flag whether the beta exercise is already visible according to its editing
        period. If no deadline is set, it counts as started.
        """
        if self.deadline and self.days_to_complete:
            end = self.deadline.replace(tzinfo=ZoneInfo(TIME_ZONE))
            start = end - timedelta(days=self.days_to_complete)
            current_time = datetime.now(ZoneInfo(TIME_ZONE))
            return current_time > start
        return True

    @property
    def deadline_exceeded(self) -> bool:
        """Flag whether the beta exercise deadline is over."""
        if self.deadline:
            deadline = self.deadline.replace(tzinfo=ZoneInfo(TIME_ZONE))
            return datetime.now(ZoneInfo(TIME_ZONE)) > deadline
        return False

    def __repr__(self):
        return f"<BetaExercise(id={self.id}, title='{self.title}')>"


class BetaExerciseResult(SQLModel, table=True):
    """Per-student persisted Beta AI chat state for one beta exercise.

    This intentionally does not reuse the regular ExerciseResult table. It stores
    the student-facing Beta AI conversation independently from later didactic
    trace logs, student concept state, and completion logic.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_text: List[Dict[str, Any]] = Field(sa_column=Column(JSON), default=[])
    finished_conversation: List[Dict[str, Any]] = Field(
        sa_column=Column(JSON), default=[]
    )
    completion_unlocked: bool = Field(default=False)
    completed_at: Optional[datetime] = Field(
        sa_column=Column(type_=DateTime(timezone=True)), default=None
    )
    submit_time_stamp: Optional[datetime] = Field(
        sa_column=Column(type_=DateTime(timezone=True)), default=None
    )
    started_at: Optional[datetime] = Field(
        sa_column=Column(type_=DateTime(timezone=True)), default=None
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(type_=DateTime(timezone=True)), default=None
    )

    # database relationships
    beta_exercise_id: int = Field(foreign_key="betaexercise.id", ondelete="CASCADE")
    userinfo_id: int = Field(foreign_key="userinfo.id", ondelete="CASCADE")

    def __repr__(self):
        return (
            f"<BetaExerciseResult(beta_exercise_id={self.beta_exercise_id}, "
            f"userinfo_id={self.userinfo_id})>"
        )


class BetaExerciseTraceLog(SQLModel, table=True):
    """Replayable didactic trace for one Beta AI chat turn.

    Each row represents one student answer and the resulting diagnosis, policy
    decision, tutor turn, and state snapshot. BetaExerciseResult remains the
    conversation-level container; this table stores append-only per-turn audit
    events so traces can be queried and evaluated without growing JSON blobs.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    beta_exercise_result_id: int = Field(
        foreign_key="betaexerciseresult.id", ondelete="CASCADE", index=True
    )
    beta_exercise_id: int = Field(
        foreign_key="betaexercise.id", ondelete="CASCADE", index=True
    )
    userinfo_id: int = Field(foreign_key="userinfo.id", ondelete="CASCADE", index=True)
    beta_concept_id: Optional[int] = Field(
        default=None, foreign_key="betaconcept.id", ondelete="SET NULL", index=True
    )
    turn_index: int = Field(default=0, index=True)
    concept_label: str = Field(nullable=False, default="")
    student_answer: str = Field(nullable=False, default="")
    final_pattern: str = Field(nullable=False, default="")
    selected_action: str = Field(nullable=False, default="")
    selected_rule_id: str = Field(nullable=False, default="")
    question_level: str = Field(nullable=False, default="")
    trace_entry: Dict[str, Any] = Field(sa_column=Column(JSON), default={})
    created_at: Optional[datetime] = Field(
        sa_column=Column(type_=DateTime(timezone=True)), default=None
    )

    def __repr__(self):
        return (
            f"<BetaExerciseTraceLog(beta_exercise_result_id="
            f"{self.beta_exercise_result_id}, turn_index={self.turn_index})>"
        )


class BetaStudentConceptState(SQLModel, table=True):
    """Minimal per-student state for one Beta AI concept.

    The state is deliberately heuristic and transparent. It is updated from the
    structured diagnosis pattern and policy action, not directly by free-form LLM
    text.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    userinfo_id: int = Field(foreign_key="userinfo.id", ondelete="CASCADE")
    beta_exercise_id: int = Field(foreign_key="betaexercise.id", ondelete="CASCADE")
    beta_concept_id: int = Field(foreign_key="betaconcept.id", ondelete="CASCADE")
    state: str = Field(nullable=False, default="unseen")
    attempts_total: int = Field(default=0)
    successful_attempts: int = Field(default=0)
    misconception_hits: int = Field(default=0)
    covered_core_point_ids: List[int] = Field(sa_column=Column(JSON), default=[])
    missing_core_point_ids: List[int] = Field(sa_column=Column(JSON), default=[])
    evidence_by_core_point: Dict[str, Any] = Field(sa_column=Column(JSON), default={})
    level_status: Dict[str, Any] = Field(sa_column=Column(JSON), default={})
    level_evidence: Dict[str, Any] = Field(sa_column=Column(JSON), default={})
    active_misconceptions: List[Dict[str, Any]] = Field(
        sa_column=Column(JSON), default=[]
    )
    resolved_misconceptions: List[Dict[str, Any]] = Field(
        sa_column=Column(JSON), default=[]
    )
    last_diagnosis_pattern: str = Field(nullable=False, default="")
    last_policy_action: str = Field(nullable=False, default="")
    updated_at: Optional[datetime] = Field(
        sa_column=Column(type_=DateTime(timezone=True)), default=None
    )

    def __repr__(self):
        return (
            f"<BetaStudentConceptState(userinfo_id={self.userinfo_id}, "
            f"beta_concept_id={self.beta_concept_id}, state='{self.state}')>"
        )


class BetaConcept(SQLModel, table=True):
    """
    Concept generated or curated for a Beta AI Tutor exercise.

    A concept is the didactic unit that later drives diagnosis, policy decisions,
    student state, and audit logs.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    beta_exercise_id: int = Field(foreign_key="betaexercise.id", ondelete="CASCADE")
    concept_id: str = Field(nullable=False, default="", index=True)
    label: str = Field(nullable=False, default="")
    description: str = Field(nullable=False, default="")
    order_index: int = Field(default=0)

    # ORM relationships
    beta_exercise: "BetaExercise" = Relationship(back_populates="concepts")
    core_points: List["BetaCorePoint"] = Relationship(
        back_populates="beta_concept", sa_relationship_kwargs={"passive_deletes": True}
    )
    misconceptions: List["BetaMisconception"] = Relationship(
        back_populates="beta_concept", sa_relationship_kwargs={"passive_deletes": True}
    )

    def __repr__(self):
        return f"<BetaConcept(id={self.id}, concept_id='{self.concept_id}')>"


class BetaCorePoint(SQLModel, table=True):
    """Expected core point that should be covered for a beta concept."""

    id: Optional[int] = Field(default=None, primary_key=True)
    beta_concept_id: int = Field(foreign_key="betaconcept.id", ondelete="CASCADE")
    text: str = Field(nullable=False, default="")
    required: bool = Field(default=True)
    order_index: int = Field(default=0)

    # ORM relationships
    beta_concept: "BetaConcept" = Relationship(back_populates="core_points")

    def __repr__(self):
        return f"<BetaCorePoint(id={self.id}, beta_concept_id={self.beta_concept_id})>"


class BetaMisconception(SQLModel, table=True):
    """Misconception hint associated with a beta concept."""

    id: Optional[int] = Field(default=None, primary_key=True)
    beta_concept_id: int = Field(foreign_key="betaconcept.id", ondelete="CASCADE")
    label: str = Field(nullable=False, default="")
    order_index: int = Field(default=0)

    # ORM relationships
    beta_concept: "BetaConcept" = Relationship(back_populates="misconceptions")

    def __repr__(self):
        return (
            f"<BetaMisconception(id={self.id}, beta_concept_id={self.beta_concept_id})>"
        )


class UserInfo(SQLModel, table=True):
    """
    Adds more attributes to a user than just name and password.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="localuser.id", ondelete="CASCADE")
    email: str
    role: UserRole
    language: Language = Field(default=Language.EN)

    # ORM relationship
    exercise_results: List["ExerciseResult"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"passive_deletes": True}
    )
    local_user: "LocalUser" = Relationship()


class Config(SQLModel, table=True):
    """
    Table for storing global configuration settings.
    """

    # make sure there is only one row in the table
    __table_args__ = (CheckConstraint("id = 1", name="only_one_row"),)

    id: Optional[int] = Field(default=1, primary_key=True)
    check_conversation_prompt: str
    response_ai_model: str
    check_ai_model: str
    how_to_use_text: str
    general_information_text: str
    lecture_information_text: str
    course_name: str
    impressum_text: str
    registration_code: str
    exercise_token_limit: int = Field(default=30000)

    def __repr__(self):
        return f"<Config(id={self.id}, course_name='{self.course_name}')>"


class Prompt(SQLModel, table=True):
    """
    Table for storing prompt templates.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, nullable=False)
    prompt_template: str = Field(nullable=False, default="")
    is_default_prompt: bool = Field(default=False)

    def __repr__(self):
        return f"<Prompt(name='{self.name}')>"


class Report(SQLModel, table=True):
    """
    Represents a report submitted for a particular exercise.

    Attributes:
        id: Primary key of the report.
        exercise_id: Foreign key referencing the associated Exercise
        (nullable if exercise deleted).
        userinfo_id: Foreign key referencing the user who submitted the report.
        report_text: The text content of the report.
        looked_at: Flag indicating whether the report has been viewed by a tutor.
        conversation_snapshot: Snapshot of the conversation at report submission time.
        exercise: Relationship to the associated Exercise (may be None if deleted).
        user: Relationship to the user who submitted the report.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    exercise_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            "exercise_id",
            sa.Integer,
            SAForeignKey(
                "exercise.id", ondelete="SET NULL", name="fk_report_exercise_id"
            ),
            nullable=True,
        ),
    )
    userinfo_id: int = Field(
        foreign_key="userinfo.id", nullable=False, ondelete="CASCADE"
    )
    report_text: str
    looked_at: bool = Field(default=False)
    conversation_snapshot: List[Dict[str, Any]] = Field(
        sa_column=Column(JSON), default=[]
    )

    exercise: Optional["Exercise"] = Relationship()
    userinfo: "UserInfo" = Relationship()
