"""Page for lecture tutors/owners to see lecture-specific reports."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_lecture_role
from aitutor.models import LectureRole
from aitutor.pages.lecture_reports.components import lecture_reports_table
from aitutor.pages.lecture_reports.state import LectureReportsState
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_specific_lecture import with_specific_lecture_navbar
from aitutor.utilities.filtering_components import search_badges, search_bar


@page_require_lecture_role(LectureRole.TUTOR)
@with_navbar(routes.LECTURES)
@with_specific_lecture_navbar(
    "reports",
    LectureReportsState.current_lecture_id,
)
def lecture_reports_page() -> rx.Component:
    """Lecture-specific reports page."""
    return rx.center(
        lecture_reports_content(),
        margin_top="2em",
        margin_bottom="2em",
        width="100%",
    )


def lecture_reports_content() -> rx.Component:
    """Render lecture reports content."""
    return rx.vstack(
        search_bar(LectureReportsState),
        search_badges(LectureReportsState),
        lecture_reports_table(),
        align="center",
        justify="center",
    )
