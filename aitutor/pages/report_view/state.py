"""State for the Report View page."""

import reflex as rx
from sqlmodel import select
from sqlalchemy.orm import selectinload

from aitutor.auth.state import SessionState
from aitutor.models import Report, ExerciseResult, Exercise, UserInfo, UserRole
from aitutor.auth.protection import state_require_role_at_least
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
                    selectinload(Report.exercise_result)
                    .selectinload(ExerciseResult.exercise),
                    selectinload(Report.exercise_result)
                    .selectinload(ExerciseResult.user)
                    .selectinload(UserInfo.local_user),
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
                # Use finished_conversation if available, otherwise use conversation_text
                conversation_data = (
                    exercise_result.finished_conversation 
                    if exercise_result.finished_conversation 
                    else exercise_result.conversation_text
                )
                
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
