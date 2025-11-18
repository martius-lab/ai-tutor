"""Components for the reports page."""


import reflex as rx
from aitutor.pages.reports.state import ReportState

def report_modal():
    """An alert/dialog with a textarea for the report text.

    Usage: include ReportState.report_modal_open as the `open` condition
    and bind the textarea to ReportState.set_report_text, the confirm to confirm_report.
    """

    # We'll use rx.alert_dialog which is common in Reflex examples.
    return rx.alert_dialog.root(
        rx.alert_dialog.overlay(
            rx.alert_dialog.content(
                rx.alert_dialog.header(rx.text("Report conversation")),
                rx.alert_dialog.body(
                    rx.vstack(
                        rx.text(
                            "Please describe what went wrong (optional). The admin will review this conversation."
                        ),
                        rx.text_area(
                            placeholder="Short description of the problem",
                            value=ReportState.report_text,
                            on_change=ReportState.set_report_text,
                            min_height="120px",
                        ),
                        spacing="4",
                    )
                ),
                rx.alert_dialog.footer(
                    rx.button("Cancel", on_click=ReportState.close_report_modal),
                    rx.button("Submit report", on_click=ReportState.confirm_report),
                    spacing="3",
                ),
                size="4",
            ),
        ),
        open=ReportState.report_modal_open,
        is_centered=True,
    )
