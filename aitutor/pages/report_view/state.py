"""State for the Report View page."""

import reflex as rx
from sqlalchemy.orm import selectinload
from sqlmodel import select

from aitutor.auth.protection import state_require_role_at_least
from aitutor.auth.state import SessionState
from aitutor.models import ExerciseResult, Report, UserInfo, UserRole
from aitutor.pages.chat.state import ChatMessage, Role


class ReportViewState(SessionState):
    """State for viewing a specific report."""

    report_text: str = ""
    looked_at: bool = False
    exercise_title: str = ""
    username: str = ""
    messages: list[ChatMessage] = []

    @rx.event
    @state_require_role_at_least(UserRole.TUTOR)
    def on_load(self):
        """Load report details when page opens."""
        self.global_load()
        self.load_report()

    def on_logout(self):
        """Clear state when user logs out."""
        self.report_text = ""
        self.looked_at = False
        self.exercise_title = ""
        self.username = ""
        self.messages = []

    @rx.event
    def load_report(self):
        """Load report and associated conversation from database."""
        with rx.session() as session:
            # Load report with all needed relationships
            report = session.exec(
                select(Report)
                .where(Report.id == self.report_id)
                .options(
                    selectinload(Report.exercise_result).selectinload(  # type: ignore
                        ExerciseResult.exercise  # type: ignore
                    ),
                    selectinload(Report.exercise_result)  # type: ignore
                    .selectinload(ExerciseResult.user)  # type: ignore
                    .selectinload(UserInfo.local_user),  # type: ignore
                )
            ).first()

            if report:
                self.report_text = report.report_text
                self.looked_at = report.looked_at

                # Mark report as looked at if not already
                if not report.looked_at:
                    report.looked_at = True
                    session.add(report)
                    session.commit()
                    self.looked_at = True

                # Get exercise and user info
                exercise_result = report.exercise_result
                self.exercise_title = exercise_result.exercise.title
                self.username = exercise_result.user.local_user.username

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
    @state_require_role_at_least(UserRole.TUTOR)
    def toggle_looked_at(self):
        """Toggle the looked_at status of the report."""
        with rx.session() as session:
            report = session.exec(
                select(Report).where(Report.id == self.report_id)
            ).first()

            if report:
                report.looked_at = not report.looked_at
                session.add(report)
                session.commit()
                self.looked_at = report.looked_at
