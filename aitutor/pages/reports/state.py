"""State for the reports page."""

from dataclasses import dataclass
from typing import override

import reflex as rx
from sqlalchemy import and_, or_
from sqlalchemy.orm import selectinload
from sqlmodel import select

import aitutor.global_vars as gv
from aitutor.auth.protection import state_require_role_at_least
from aitutor.auth.state import SessionState
from aitutor.models import (
    Exercise,
    ExerciseResult,
    LocalUser,
    Report,
    Tag,
    UserInfo,
    UserRole,
)
from aitutor.utilities.filtering_components import FilterMixin


@dataclass
class TableRow:
    """A row in the reports table."""

    report_id: int
    username: str
    exercise_title: str
    report_preview: str  # First 30 characters
    looked_at: bool


class ReportsState(FilterMixin, SessionState):
    """State for the reports page."""

    table_rows: list[TableRow]

    # valid search keys
    search_keys: list[str] = [
        gv.SEARCH_USER_KEY,
        gv.SEARCH_EXERCISE_KEY,
    ]

    @rx.event
    @state_require_role_at_least(UserRole.TUTOR)
    def on_load(self):
        """Load all reports when page opens."""
        self.global_load()
        self.load_reports()

    def on_logout(self):
        """Clear state when user logs out."""
        self.table_rows = []
        self.search_values = []

    @override
    @rx.event
    def load_filtered_data(self):
        """Implements the abstract method from FilterMixin."""
        self.load_reports()

    @rx.event
    def load_reports(self):
        """Fetch reports from the database with filtering."""
        with rx.session() as session:
            # Build query with all necessary relationships
            stmt = (
                select(Report)
                .options(
                    selectinload(Report.exercise_result)
                    .selectinload(ExerciseResult.exercise)
                    .selectinload(Exercise.tags),
                    selectinload(Report.exercise_result)
                    .selectinload(ExerciseResult.user)
                    .selectinload(UserInfo.local_user),
                )
                .order_by(Report.id.desc())
            )

            # Apply search filters if any
            if self.search_values:
                search_conditions = []
                for key, value in self.search_values:
                    match key:
                        case gv.SEARCH_USER_KEY:
                            stmt = (
                                stmt.join(ExerciseResult, Report.exercise_result)
                                .join(UserInfo, ExerciseResult.user)
                                .join(LocalUser, UserInfo.local_user)
                            )
                            search_conditions.append(
                                LocalUser.username.ilike(f"%{value}%")
                            )
                        case gv.SEARCH_EXERCISE_KEY:
                            stmt = stmt.join(
                                ExerciseResult, Report.exercise_result
                            ).join(Exercise, ExerciseResult.exercise)
                            search_conditions.append(Exercise.title.ilike(f"%{value}%"))

                        case _:
                            # General search across all fields
                            stmt = (
                                stmt.join(ExerciseResult, Report.exercise_result)
                                .join(UserInfo, ExerciseResult.user)
                                .join(LocalUser, UserInfo.local_user)
                                .join(Exercise, ExerciseResult.exercise)
                            )
                            search_conditions.append(
                                or_(
                                    LocalUser.username.ilike(f"%{value}%"),
                                    Exercise.title.ilike(f"%{value}%"),
                                    Exercise.tags.any(Tag.name.ilike(f"%{value}%")),
                                    Report.report_text.ilike(f"%{value}%"),
                                )
                            )

                if search_conditions:
                    stmt = stmt.where(and_(*search_conditions))

            # Execute query
            reports = session.exec(stmt).all()

            # Convert to TableRow format
            self.table_rows = [
                TableRow(
                    report_id=report.id,
                    username=report.exercise_result.user.local_user.username,
                    exercise_title=report.exercise_result.exercise.title,
                    report_preview=report.report_text[:30] + "..."
                    if len(report.report_text) > 30
                    else report.report_text,
                    looked_at=report.looked_at,
                )
                for report in reports
            ]

    @rx.event
    @state_require_role_at_least(UserRole.TUTOR)
    def toggle_looked_at(self, report_id: int):
        """Toggle the looked_at status of a report."""
        with rx.session() as session:
            report = session.exec(select(Report).where(Report.id == report_id)).first()

            if report:
                report.looked_at = not report.looked_at
                session.add(report)
                session.commit()

                # Reload reports to update UI
                self.load_reports()

    @rx.event
    @state_require_role_at_least(UserRole.TUTOR)
    def delete_report(self, report_id: int):
        """Delete a report from the database."""
        with rx.session() as session:
            report = session.exec(select(Report).where(Report.id == report_id)).first()

            if report:
                session.delete(report)
                session.commit()

                # Reload reports to update UI
                self.load_reports()
