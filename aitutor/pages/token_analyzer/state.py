"""State for the token analyzer page."""

from dataclasses import dataclass
from math import floor, log10

import reflex as rx
from sqlmodel import func, select

from aitutor.auth.protection import state_require_role_at_least
from aitutor.auth.state import SessionState
from aitutor.models import Exercise, ExerciseResult, LocalUser, UserInfo, UserRole

ALL_EXERCISES_OPTION = "All"
ALL_USERS_OPTION = "All"


@dataclass
class TableRow:
    """A row in the token analyzer table."""

    username: str
    tokens_used: int


@dataclass
class ExerciseTableRow:
    """A row in the exercise token analyzer table."""

    exercise_title: str
    tokens_used: int


class TokenAnalyzerState(SessionState):
    """State for the token analyzer page."""

    table_rows: list[TableRow]
    chart_data: list[dict[str, int | float]]
    chart_ticks: list[int]
    exercise_options: list[str]
    selected_exercise_name: str = ALL_EXERCISES_OPTION

    exercise_table_rows: list[ExerciseTableRow]
    exercise_chart_data: list[dict[str, int | float]]
    exercise_chart_ticks: list[int]
    user_options: list[str]
    selected_user_name: str = ALL_USERS_OPTION

    @rx.var
    def chart_min_width(self) -> str:
        """Minimum chart width to keep bars readable for many users."""
        chart_count = len(self.chart_data)
        if chart_count > 120:
            return "1400px"
        if chart_count > 80:
            return "1000px"
        return "700px"

    @rx.var
    def exercise_chart_min_width(self) -> str:
        """Minimum chart width to keep bars readable for many exercises."""
        chart_count = len(self.exercise_chart_data)
        if chart_count > 120:
            return "1400px"
        if chart_count > 80:
            return "1000px"
        return "700px"

    @rx.event
    @state_require_role_at_least(UserRole.ADMIN)
    def on_load(self):
        """Gets executed when the page loads."""
        self.global_load()
        self.load_exercise_options()
        self.load_user_options()
        self.load_token_rows()
        self.load_exercise_token_rows()

    def on_logout(self):
        """Clears the state when the user logs out."""
        self.table_rows = []
        self.chart_data = []
        self.chart_ticks = []
        self.exercise_options = []
        self.selected_exercise_name = ALL_EXERCISES_OPTION
        self.exercise_table_rows = []
        self.exercise_chart_data = []
        self.exercise_chart_ticks = []
        self.user_options = []
        self.selected_user_name = ALL_USERS_OPTION

    @rx.event
    def load_exercise_options(self):
        """Load selectable exercises for filtering."""
        with rx.session() as session:
            exercises = session.exec(
                select(Exercise.title).order_by(func.lower(Exercise.title))
            ).all()
            self.exercise_options = [ALL_EXERCISES_OPTION, *exercises]

    @rx.event
    def set_selected_exercise_name(self, exercise_name: str):
        """Set selected exercise filter and reload the token rows."""
        self.selected_exercise_name = exercise_name
        self.load_token_rows()

    @rx.event
    def load_user_options(self):
        """Load selectable users for filtering the exercise analysis."""
        with rx.session() as session:
            users = session.exec(
                select(LocalUser.username).order_by(func.lower(LocalUser.username))
            ).all()
            self.user_options = [ALL_USERS_OPTION, *users]

    @rx.event
    def set_selected_user_name(self, user_name: str):
        """Set selected user filter and reload exercise token rows."""
        self.selected_user_name = user_name
        self.load_exercise_token_rows()

    @staticmethod
    def _build_rank_ticks(total_items: int) -> list[int]:
        """Build mathematically nice rank ticks with roughly 8 markers."""
        if total_items == 0:
            return []

        target_tick_count = 8
        raw_step = max(1.0, (total_items - 1) / max(1, target_tick_count - 1))
        magnitude = 10 ** floor(log10(raw_step))
        step = magnitude
        for multiplier in (1, 2, 5, 10):
            candidate = multiplier * magnitude
            if candidate >= raw_step:
                step = candidate
                break

        tick_set = {1, total_items}
        tick_set.update(range(step, total_items, step))
        return sorted(tick_set)

    @rx.event
    def load_token_rows(self):
        """Load total token usage per user.

        Sort order:
        1. tokens_used descending
        2. username ascending
        """
        with rx.session() as session:
            total_tokens = func.sum(ExerciseResult.tokens_used)

            stmt = select(LocalUser.username, total_tokens).select_from(LocalUser)
            stmt = stmt.join(UserInfo).join(ExerciseResult)

            if self.selected_exercise_name != ALL_EXERCISES_OPTION:
                stmt = stmt.join(Exercise).where(Exercise.title == self.selected_exercise_name)

            stmt = stmt.group_by(LocalUser.username).order_by(
                total_tokens.desc(), func.lower(LocalUser.username)
            )

            self.table_rows = [
                TableRow(username=username, tokens_used=tokens_used)
                for username, tokens_used in session.exec(stmt).all()
            ]

            self.chart_data = [
                {
                    "rank": index + 1,
                    "tokens_used": row.tokens_used,
                    "tokens_used_k": round(row.tokens_used / 1000, 1),
                }
                for index, row in enumerate(self.table_rows)
            ]
            self.chart_ticks = self._build_rank_ticks(len(self.table_rows))

    @rx.event
    def load_exercise_token_rows(self):
        """Load total token usage per exercise.

        Sort order:
        1. tokens_used descending
        2. exercise_title ascending
        """
        with rx.session() as session:
            total_tokens = func.sum(ExerciseResult.tokens_used)

            stmt = select(Exercise.title, total_tokens).select_from(Exercise)
            stmt = stmt.join(ExerciseResult).join(UserInfo).join(LocalUser)

            if self.selected_user_name != ALL_USERS_OPTION:
                stmt = stmt.where(LocalUser.username == self.selected_user_name)

            stmt = stmt.group_by(Exercise.title).order_by(
                total_tokens.desc(), func.lower(Exercise.title)
            )

            self.exercise_table_rows = [
                ExerciseTableRow(exercise_title=exercise_title, tokens_used=tokens_used)
                for exercise_title, tokens_used in session.exec(stmt).all()
            ]

            self.exercise_chart_data = [
                {
                    "rank": index + 1,
                    "tokens_used": row.tokens_used,
                    "tokens_used_k": round(row.tokens_used / 1000, 1),
                }
                for index, row in enumerate(self.exercise_table_rows)
            ]
            self.exercise_chart_ticks = self._build_rank_ticks(
                len(self.exercise_table_rows)
            )
