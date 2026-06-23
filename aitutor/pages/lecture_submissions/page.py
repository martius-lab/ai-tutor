"""Page for lecture tutors/owners to see lecture-specific submissions."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_lecture_role
from aitutor.models import LectureRole
from aitutor.pages.lecture_submissions.components import lecture_submissions_table
from aitutor.pages.lecture_submissions.state import LectureSubmissionsState
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_specific_lecture import with_specific_lecture_navbar
from aitutor.utilities.filtering_components import search_badges, search_bar


def lecture_submissions_content() -> rx.Component:
    """Render lecture submissions content."""
    return rx.vstack(
        search_bar(LectureSubmissionsState),
        search_badges(LectureSubmissionsState),
        lecture_submissions_table(),
        align="center",
        justify="center",
    )


@page_require_lecture_role(LectureRole.TUTOR)
@with_navbar(routes.LECTURES)
@with_specific_lecture_navbar(
    "submissions",
    LectureSubmissionsState.current_lecture_id,
)
def lecture_submissions_page() -> rx.Component:
    """Lecture-specific submissions page."""
    return rx.center(
        lecture_submissions_content(),
        margin_top="2em",
        margin_bottom="2em",
        width="90%",
    )
