"""State for the token analyzer page."""

from dataclasses import dataclass

import reflex as rx
from sqlmodel import func, select

from aitutor.auth.protection import state_require_role_at_least
from aitutor.auth.state import SessionState
from aitutor.models import ExerciseResult, LocalUser, UserInfo, UserRole


@dataclass
class TableRow:
    """A row in the token analyzer table."""

    username: str
    tokens_used: int


class TokenAnalyzerState(SessionState):
    """State for the token analyzer page."""

    table_rows: list[TableRow]

    @rx.event
    @state_require_role_at_least(UserRole.ADMIN)
    def on_load(self):
        """Gets executed when the page loads."""
        self.global_load()
        self.load_token_rows()

    def on_logout(self):
        """Clears the state when the user logs out."""
        self.table_rows = []

    @rx.event
    def load_token_rows(self):
        """Load total token usage per user.

        Sort order:
        1. tokens_used descending
        2. username ascending
        """
        with rx.session() as session:
            total_tokens = func.sum(ExerciseResult.tokens_used)

            stmt = (
                select(LocalUser.username, total_tokens)
                .select_from(LocalUser)
                .join(UserInfo)
                .join(ExerciseResult)
                .group_by(LocalUser.username)
                .order_by(total_tokens.desc(), func.lower(LocalUser.username))
            )

            self.table_rows = [
                TableRow(username=username, tokens_used=tokens_used)
                for username, tokens_used in session.exec(stmt).all()
            ]
