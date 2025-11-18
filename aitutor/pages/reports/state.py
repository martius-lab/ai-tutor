"""The state for the reports page."""

import reflex as rx
from aitutor.auth.state import SessionState
from aitutor.auth.protection import state_require_role_at_least
from aitutor.models import UserRole, Report
from typing import Optional


class ReportsState(SessionState):
    """The State for the reports page."""

    @rx.event
    @state_require_role_at_least(UserRole.TUTOR)
    def on_load(self):
        """Initialization for the page."""
        self.global_load()

    def on_logout(self):
        """Clears the state when the user logs out."""


class ReportState(SessionState):
    """
    State for reporting a conversation.
    This is lightweight: it can be mounted into pages/components that need it.
    """

    # UI state
    report_modal_open: bool = False
    report_text: str = ""
    reported_result_id: Optional[int] = None

    @rx.event
    def open_report_modal(self, result_id: int):
        """Open the modal and set the result id."""
        self.reported_result_id = result_id
        self.report_text = ""
        self.report_modal_open = True

    @rx.event
    def close_report_modal(self):
        """Close modal without saving."""
        self.report_modal_open = False
        self.report_text = ""
        self.reported_result_id = None

    @rx.event
    def set_report_text(self, value: str):
        self.report_text = value

    @rx.event
    def confirm_report(self):
        """Save report to DB and close modal. No role restriction for reporting (students)."""
        if not self.reported_result_id:
            # nothing to save
            self.report_modal_open = False
            return

        # Save to DB
        with rx.session() as session:
            repo = Report(
                exercise_result_id=int(self.reported_result_id),
                report_text=self.report_text or "",
                looked_at=False,
            )
            session.add(repo)
            session.commit()

        # small feedback
        rx.toast("Report submitted. Thank you.")
        self.report_modal_open = False
        self.report_text = ""
        self.reported_result_id = None