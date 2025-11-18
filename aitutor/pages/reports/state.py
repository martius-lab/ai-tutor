"""State for the reports page."""

import reflex as rx
from sqlmodel import select
from aitutor.models import Report

class ReportsState(rx.State):
    reports: list[Report] = []

    @rx.event
    def on_load(self):
        """Load all reports when page opens."""
        self.load_reports()

    @rx.event
    def load_reports(self):
        """Fetch reports from the database."""
        with rx.session() as session:
            self.reports = list(session.exec(select(Report)).all())
