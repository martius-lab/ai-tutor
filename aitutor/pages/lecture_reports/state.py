"""State for the lecture-specific reports page."""

from dataclasses import dataclass
from typing import override

import reflex as rx
from sqlalchemy import and_, or_
from sqlalchemy.orm import selectinload
from sqlmodel import select

import aitutor.global_vars as gv
import aitutor.routes as routes
from aitutor.auth.protection import state_require_role_or_permission
from aitutor.auth.state import SessionState
from aitutor.models import (
    Exercise,
    Lecture,
    LocalUser,
    Report,
    UserInfo,
    UserRole,
)
from aitutor.utilities.filtering_components import FilterMixin
from aitutor.utilities.lecture_permissions import user_may_view_lecture_submissions

REPORT_PREVIEW_LENGTH = 20  # Number of characters to show in table preview


@dataclass
class LectureReportTableRow:
    """A row in the lecture-specific reports table."""

    report_id: int | None
    report_view_route: str
    username: str
    exercise_title: str | None
    report_preview: str
    looked_at: bool


class LectureReportsState(FilterMixin, SessionState):
    """State for the lecture-specific reports page."""

    current_lecture_id: int | None = None
    table_rows: list[LectureReportTableRow]

    # valid search keys
    search_keys: list[str] = [
        gv.SEARCH_USER_KEY,
        gv.SEARCH_EXERCISE_KEY,
    ]

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.STUDENT)
    def on_load(self):
        """Load all reports for the current lecture when page opens."""
        self.global_load()
        self.current_lecture_id = None
        self.table_rows = []

        try:
            lecture_id = int(self.lecture_id)
        except ValueError:
            return rx.redirect(routes.NOT_FOUND)

        if not self._user_may_view_reports(lecture_id):
            return rx.redirect(routes.MY_LECTURES)

        with rx.session() as session:
            if session.get(Lecture, lecture_id) is None:
                return rx.redirect(routes.NOT_FOUND)

        self.current_lecture_id = lecture_id
        self.load_reports()

    def on_logout(self):
        """Clear state when user logs out."""
        self.current_lecture_id = None
        self.table_rows = []
        self.search_values = []

    @override
    @rx.event
    def load_filtered_data(self):
        """Implements the abstract method from FilterMixin."""
        self.load_reports()

    @rx.event
    def load_reports(self):
        """Fetch lecture-specific reports from the database with filtering."""
        if self.current_lecture_id is None:
            self.table_rows = []
            return

        with rx.session() as session:
            # Build query with all necessary relationships.
            # Report.lecture_id is kept even when the exercise is deleted, so deleted
            # exercises can still be shown as "Deleted" in the lecture-specific table.
            stmt = (
                select(Report)
                .where(Report.lecture_id == self.current_lecture_id)
                .options(
                    selectinload(Report.exercise),  # type: ignore
                    selectinload(Report.userinfo).selectinload(UserInfo.local_user),  # type: ignore
                )
                .order_by(Report.id.desc())  # type: ignore
            )

            # Apply search filters if any
            if self.search_values:
                search_conditions = []
                for key, value in self.search_values:
                    match key:
                        case gv.SEARCH_USER_KEY:
                            stmt = stmt.join(UserInfo, Report.userinfo).join(  # type: ignore
                                LocalUser,
                                UserInfo.local_user,  # type: ignore
                            )  # type: ignore
                            search_conditions.append(
                                LocalUser.username.ilike(f"%{value}%")  # type: ignore
                            )
                        case gv.SEARCH_EXERCISE_KEY:
                            stmt = stmt.outerjoin(Exercise, Report.exercise)  # type: ignore
                            search_conditions.append(Exercise.title.ilike(f"%{value}%"))  # type: ignore

                        case _:
                            stmt = (
                                stmt.join(UserInfo, Report.userinfo)  # type: ignore
                                .join(LocalUser, UserInfo.local_user)  # type: ignore
                                .outerjoin(Exercise, Report.exercise)  # type: ignore
                            )
                            search_conditions.append(
                                or_(
                                    LocalUser.username.ilike(f"%{value}%"),  # type: ignore
                                    Exercise.title.ilike(f"%{value}%"),  # type: ignore
                                    Report.report_text.ilike(f"%{value}%"),  # type: ignore
                                )
                            )

                if search_conditions:
                    stmt = stmt.where(and_(*search_conditions))

            # Execute query
            reports = session.exec(stmt).all()

            # Convert to LectureReportTableRow format
            self.table_rows = []

            for report in reports:
                # Determine the report preview text
                if len(report.report_text) > REPORT_PREVIEW_LENGTH:
                    preview = report.report_text[:REPORT_PREVIEW_LENGTH] + "..."
                else:
                    preview = report.report_text

                exercise_title = report.exercise.title if report.exercise else None

                # Append a LectureReportTableRow
                self.table_rows.append(
                    LectureReportTableRow(
                        report_id=report.id,
                        report_view_route=(
                            f"{routes.LECTURE_REPORT_VIEW}/"
                            f"{self.current_lecture_id}/{report.id}"
                        ),
                        username=report.userinfo.local_user.username,
                        exercise_title=exercise_title,
                        report_preview=preview,
                        looked_at=report.looked_at,
                    )
                )

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.STUDENT)
    def toggle_looked_at(self, report_id: int):
        """Toggle the looked_at status of a lecture-specific report."""
        if self.current_lecture_id is None:
            return rx.redirect(routes.MY_LECTURES)

        with rx.session() as session:
            report = session.exec(
                select(Report)
                .where(
                    Report.id == report_id,
                    Report.lecture_id == self.current_lecture_id,
                )
            ).first()

            if report:
                report.looked_at = not report.looked_at
                session.add(report)
                session.commit()

                # Reload reports to update UI
                self.load_reports()

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.STUDENT)
    def delete_report(self, report_id: int):
        """Delete a lecture-specific report from the database."""
        if self.current_lecture_id is None:
            return rx.redirect(routes.MY_LECTURES)

        with rx.session() as session:
            report = session.exec(
                select(Report)
                .where(
                    Report.id == report_id,
                    Report.lecture_id == self.current_lecture_id,
                )
            ).first()

            if report:
                session.delete(report)
                session.commit()

                # Reload reports to update UI
                self.load_reports()

    def _user_may_view_reports(self, lecture_id: int) -> bool:
        """Return whether the current user may view reports in the lecture."""
        if self.authenticated_user is None or self.authenticated_user.id is None:
            return False

        with rx.session() as session:
            return user_may_view_lecture_submissions(
                session,
                user_id=self.authenticated_user.id,
                global_permissions=self.global_permissions,
                lecture_id=lecture_id,
            )
