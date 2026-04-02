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
USER_ANALYSIS_VIEW = "user"
EXERCISE_ANALYSIS_VIEW = "exercise"


@dataclass
class TableRow:
    """A row in the token analyzer table."""

    rank: int
    username: str
    tokens_used: int


@dataclass
class ExerciseTableRow:
    """A row in the exercise token analyzer table."""

    rank: int
    exercise_title: str
    tokens_used: int


class TokenAnalyzerState(SessionState):
    """State for the token analyzer page."""

    table_rows: list[TableRow]
    chart_data: list[dict[str, int | float | str]]
    chart_ticks: list[int]
    active_analysis_view: str = USER_ANALYSIS_VIEW
    exercise_options: list[str]
    selected_exercise_name: str = ALL_EXERCISES_OPTION
    exercise_filter_query: str = ""

    exercise_table_rows: list[ExerciseTableRow]
    exercise_chart_data: list[dict[str, int | float | str]]
    exercise_chart_ticks: list[int]
    exercise_bar_size: int = 3
    user_options: list[str]
    selected_user_name: str = ALL_USERS_OPTION
    user_filter_query: str = ""
    user_bar_size: int = 3

    @rx.var
    def filtered_exercise_options(self) -> list[str]:
        """Exercise options filtered by the search query."""
        query = self.exercise_filter_query.strip().lower()
        if not query:
            return self.exercise_options

        filtered = [
            option
            for option in self.exercise_options
            if option == ALL_EXERCISES_OPTION or option.lower().startswith(query)
        ]
        return filtered or [ALL_EXERCISES_OPTION]

    @rx.var
    def filtered_user_options(self) -> list[str]:
        """User options filtered by the search query."""
        query = self.user_filter_query.strip().lower()
        if not query:
            return self.user_options

        filtered = [
            option
            for option in self.user_options
            if option == ALL_USERS_OPTION or option.lower().startswith(query)
        ]
        return filtered or [ALL_USERS_OPTION]

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

    @staticmethod
    def _get_dynamic_bar_size(chart_count: int) -> int:
        """Dynamic chart bar size based on number of bars."""
        if chart_count <= 20:
            return 14
        if chart_count <= 40:
            return 10
        if chart_count <= 70:
            return 7
        if chart_count <= 110:
            return 5
        return 3

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
        self.active_analysis_view = USER_ANALYSIS_VIEW
        self.exercise_options = []
        self.selected_exercise_name = ALL_EXERCISES_OPTION
        self.exercise_filter_query = ""
        self.exercise_table_rows = []
        self.exercise_chart_data = []
        self.exercise_chart_ticks = []
        self.exercise_bar_size = 3
        self.user_options = []
        self.selected_user_name = ALL_USERS_OPTION
        self.user_filter_query = ""
        self.user_bar_size = 3

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
    def set_active_analysis_view(self, view: str):
        """Set which analysis block is visible on the page."""
        if view in (USER_ANALYSIS_VIEW, EXERCISE_ANALYSIS_VIEW):
            self.active_analysis_view = view

    @rx.event
    def set_exercise_filter_query(self, query: str):
        """Set the exercise search query for the selector."""
        self.exercise_filter_query = query

    @rx.event
    def clear_exercise_filter_query(self):
        """Clear the exercise search query."""
        self.exercise_filter_query = ""

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

    @rx.event
    def set_user_filter_query(self, query: str):
        """Set the user search query for the selector."""
        self.user_filter_query = query

    @rx.event
    def clear_user_filter_query(self):
        """Clear the user search query."""
        self.user_filter_query = ""



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
                TableRow(rank=index, username=username, tokens_used=tokens_used)
                for index, (username, tokens_used) in enumerate(
                    session.exec(stmt).all(), start=1
                )
            ]

            self.chart_data = [
                {
                    "rank": index + 1,
                    "username": row.username,
                    "tokens_used": row.tokens_used,
                    "tokens_used_k": round(row.tokens_used / 1000, 1),
                }
                for index, row in enumerate(self.table_rows)
            ]
            self.chart_ticks = self._build_rank_ticks(len(self.table_rows))
            self.user_bar_size = self._get_dynamic_bar_size(len(self.table_rows))

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
                ExerciseTableRow(
                    rank=index,
                    exercise_title=exercise_title,
                    tokens_used=tokens_used,
                )
                for index, (exercise_title, tokens_used) in enumerate(
                    session.exec(stmt).all(), start=1
                )
            ]

            self.exercise_chart_data = [
                {
                    "rank": index + 1,
                    "exercise": row.exercise_title,
                    "tokens_used": row.tokens_used,
                    "tokens_used_k": round(row.tokens_used / 1000, 1),
                }
                for index, row in enumerate(self.exercise_table_rows)
            ]
            self.exercise_chart_ticks = self._build_rank_ticks(
                len(self.exercise_table_rows)
            )
            self.exercise_bar_size = self._get_dynamic_bar_size(
                len(self.exercise_table_rows)
            )

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