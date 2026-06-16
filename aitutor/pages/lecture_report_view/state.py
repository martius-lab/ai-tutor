"""State for the lecture-specific Report View page."""

import reflex as rx
from sqlalchemy.orm import selectinload
from sqlmodel import select

import aitutor.routes as routes
from aitutor.auth.protection import state_require_role_or_permission
from aitutor.auth.state import SessionState
from aitutor.models import Lecture, Report, UserInfo, UserRole
from aitutor.pages.chat.state import ChatMessage, Role
from aitutor.utilities.lecture_permissions import user_may_view_lecture_submissions


class LectureReportViewState(SessionState):
    """State for viewing a specific report in a lecture context."""

    current_lecture_id: int | None = None
    reports_route: str = routes.MY_LECTURES
    report_text: str = ""
    looked_at: bool = False
    exercise_title: str | None = None
    username: str = ""
    messages: list[ChatMessage] = []

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.STUDENT)
    def on_load(self):
        """Load report details when page opens."""
        self.global_load()
        self.current_lecture_id = None
        self.reports_route = routes.MY_LECTURES
        self._clear_report_data()

        try:
            lecture_id = int(self.lecture_id)
        except ValueError:
            return rx.redirect(routes.NOT_FOUND)

        if not self._user_may_view_report(lecture_id):
            return rx.redirect(routes.MY_LECTURES)

        with rx.session() as session:
            if session.get(Lecture, lecture_id) is None:
                return rx.redirect(routes.NOT_FOUND)

        self.current_lecture_id = lecture_id
        self.reports_route = f"{routes.LECTURE_REPORTS}/{lecture_id}"
        self.load_report()

    def on_logout(self):
        """Clear state when user logs out."""
        self.current_lecture_id = None
        self.reports_route = routes.MY_LECTURES
        self._clear_report_data()

    @rx.event
    def load_report(self):
        """Load lecture-specific report and associated conversation from database."""
        if self.current_lecture_id is None:
            return rx.redirect(routes.MY_LECTURES)

        with rx.session() as session:
            # Load report with all needed relationships.
            # Report.lecture_id is kept even when the exercise is deleted.
            report = session.exec(
                select(Report)
                .where(
                    Report.id == int(self.report_id),
                    Report.lecture_id == self.current_lecture_id,
                )
                .options(
                    selectinload(Report.exercise),  # type: ignore
                    selectinload(Report.userinfo).selectinload(UserInfo.local_user),  # type: ignore
                )
            ).first()

            if report is None:
                return rx.redirect(routes.NOT_FOUND)

            self.report_text = report.report_text
            self.looked_at = report.looked_at

            # Mark report as looked at if not already
            if not report.looked_at:
                report.looked_at = True
                session.add(report)
                session.commit()
                self.looked_at = True

            # Get exercise and user info from report
            self.exercise_title = report.exercise.title if report.exercise else None
            self.username = report.userinfo.local_user.username

            # Convert conversation to ChatMessage format
            # Use the snapshot from the report instead of live conversation
            # This ensures the conversation shown is exactly as it was when reported
            conversation_data = report.conversation_snapshot

            self.messages = [
                ChatMessage(
                    role=Role(msg["role"]),
                    message=msg["content"],
                    check_passed=msg.get("check_passed", False),
                )
                for msg in conversation_data
            ]

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.STUDENT)
    def toggle_looked_at(self):
        """Toggle the looked_at status of the lecture-specific report."""
        if self.current_lecture_id is None:
            return rx.redirect(routes.MY_LECTURES)

        with rx.session() as session:
            report = session.exec(
                select(Report)
                .where(
                    Report.id == int(self.report_id),
                    Report.lecture_id == self.current_lecture_id,
                )
            ).first()

            if report:
                report.looked_at = not report.looked_at
                session.add(report)
                session.commit()
                self.looked_at = report.looked_at

    def _user_may_view_report(self, lecture_id: int) -> bool:
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

    def _clear_report_data(self):
        """Clear loaded report data."""
        self.report_text = ""
        self.looked_at = False
        self.exercise_title = ""
        self.username = ""
        self.messages = []
