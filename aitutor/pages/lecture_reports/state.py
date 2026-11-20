"""State for the lecture-specific reports page."""

from dataclasses import dataclass
from typing import override

import reflex as rx
from sqlmodel import col, select

from aitutor import routes
from aitutor.auth.protection import state_require_lecture_role
from aitutor.auth.state import SessionState
from aitutor.models import (
    Exercise,
    Lecture,
    LectureRole,
    LocalUser,
    Report,
    UserInfo,
)
from aitutor.search.query import SearchFields, any_of, contains
from aitutor.search.state import SearchKey, SearchMixin
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


class LectureReportsState(SearchMixin, SessionState):
    """State for the lecture-specific reports page."""

    current_lecture_id: int | None = None
    table_rows: list[LectureReportTableRow]

    # valid search keys
    search_keys: list[str] = [
        SearchKey.USER,
        SearchKey.EXERCISE,
    ]

    @override
    @classmethod
    def _search_fields(cls) -> SearchFields:
        username = contains(LocalUser.username)
        exercise_title = contains(Exercise.title)
        report_text = contains(Report.report_text)

        return {
            SearchKey.USER: username,
            SearchKey.EXERCISE: exercise_title,
            SearchKey.FREE_TEXT: any_of(username, exercise_title, report_text),
        }

    @rx.event
    @state_require_lecture_role(LectureRole.TUTOR)
    def on_load(self):
        """Load all reports for the current lecture when page opens."""
        self._global_load()
        self.current_lecture_id = None
        self.table_rows = []

        try:
            lecture_id = self._get_route_param_or_error("lecture_id", dtype=int)
        except Exception:
            return rx.redirect(routes.NOT_FOUND)

        if not self._user_may_view_reports(lecture_id):
            return rx.redirect(routes.MY_LECTURES)

        with rx.session() as session:
            if session.get(Lecture, lecture_id) is None:
                return rx.redirect(routes.NOT_FOUND)

        self.current_lecture_id = lecture_id
        self.load_reports()

    @override
    @rx.event
    @state_require_lecture_role(LectureRole.TUTOR)
    def load_filtered_data(self):
        """Implements the abstract method from SearchMixin."""
        self.load_reports()

    @rx.event
    @state_require_lecture_role(LectureRole.TUTOR)
    def load_reports(self):
        """Fetch lecture-specific reports from the database with filtering."""
        if self.current_lecture_id is None:
            self.table_rows = []
            return

        with rx.session() as session:
            # Exercise is an outer join: reports on deleted exercises are kept and
            # get exercise_title=None (shown as "Deleted" in the table).
            stmt = (
                select(Report, LocalUser.username, Exercise.title)
                .select_from(Report)
                .join(UserInfo)
                .join(LocalUser)
                .outerjoin(Exercise)
                .where(Report.lecture_id == self.current_lecture_id)
                .where(self._search_condition())
                .order_by(col(Report.id).desc())
            )

            self.table_rows = [
                LectureReportTableRow(
                    report_id=report.id,
                    report_view_route=(
                        f"{routes.LECTURE_REPORT_VIEW}/"
                        f"{self.current_lecture_id}/{report.id}"
                    ),
                    username=username,
                    exercise_title=exercise_title,
                    report_preview=(
                        report.report_text[:REPORT_PREVIEW_LENGTH] + "..."
                        if len(report.report_text) > REPORT_PREVIEW_LENGTH
                        else report.report_text
                    ),
                    looked_at=report.looked_at,
                )
                for report, username, exercise_title in session.exec(stmt)
            ]

    @rx.event
    @state_require_lecture_role(LectureRole.TUTOR)
    def toggle_looked_at(self, report_id: int):
        """Toggle the looked_at status of a lecture-specific report."""
        if self.current_lecture_id is None:
            return rx.redirect(routes.MY_LECTURES)

        with rx.session() as session:
            report = session.exec(
                select(Report).where(
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
    @state_require_lecture_role(LectureRole.TUTOR)
    def delete_report(self, report_id: int):
        """Delete a lecture-specific report from the database."""
        if self.current_lecture_id is None:
            return rx.redirect(routes.MY_LECTURES)

        with rx.session() as session:
            report = session.exec(
                select(Report).where(
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
