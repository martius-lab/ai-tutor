"""Components for the lecture overview page."""

import reflex as rx

from aitutor import routes
from aitutor.components.exercises import exercise_status_overview
from aitutor.language_state import LanguageState as LS
from aitutor.pages.lecture_overview.state import LectureOverviewState
from aitutor.pages.legal_infos.loader_functions import get_privacy_notice_short


def lecture_information_content() -> rx.Component:
    """Render selected lecture details inside the overview accordion."""
    return rx.vstack(
        rx.hstack(
            rx.text(LS.lecture_name + ":", weight="bold"),
            rx.text(LectureOverviewState.lecture_name),
            align="center",
        ),
        rx.hstack(
            rx.text(LS.lecture_lecturer + ":", weight="bold"),
            rx.cond(
                LectureOverviewState.lecturer_name != "",
                rx.text(LectureOverviewState.lecturer_name),
                rx.text(LS.no_lecturer_information),
            ),
            align="center",
        ),
        rx.vstack(
            rx.text(LS.lecture_info + ":", weight="bold"),
            rx.cond(
                LectureOverviewState.lecture_information_text != "",
                rx.markdown(LectureOverviewState.lecture_information_text),
                rx.text(LS.no_lecture_details),
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        spacing="3",
        align="start",
        width="100%",
    )


def lecture_dashboard_card() -> rx.Component:
    """Render the lecture-specific dashboard card."""
    return rx.card(
        exercise_status_overview(
            headline=f"{LectureOverviewState.lecture_name} {LS.dashboard}",
            progress_value=LectureOverviewState.progress_value,
            num_total_exercises=LectureOverviewState.num_total_exercises,
            num_completed_exercises=LectureOverviewState.num_completed_exercises,
            next_deadline_task=LectureOverviewState.next_deadline_task,
        ),
        width="85vw",
        max_width="100%",
        padding="4",
    )


def lecture_info_accordion() -> rx.Component:
    """Render lecture-specific information and the privacy summary."""
    privacy_notice_short: str = get_privacy_notice_short()
    return rx.cond(
        (LectureOverviewState.lecture_information_text != "")
        | (privacy_notice_short != ""),
        rx.accordion.root(
            rx.accordion.item(
                header=LS.lecture_info,
                content=lecture_information_content(),
            ),
            rx.cond(
                privacy_notice_short != "",
                rx.accordion.item(
                    header=LS.privacy_notice_short,
                    content=rx.markdown(privacy_notice_short),
                ),
            ),
            width="85vw",
            max_width="100%",
            collapsible=True,
            variant="outline",
        ),
    )


def lecture_overview_content() -> rx.Component:
    """Main content for the lecture overview page."""
    return rx.vstack(
        rx.hstack(
            rx.button(
                rx.icon("arrow-left", size=20),
                LS.my_lectures,
                on_click=rx.redirect(routes.MY_LECTURES),
                _hover={"cursor": "pointer"},
            ),
            width="85vw",
            max_width="100%",
        ),
        lecture_dashboard_card(),
        lecture_info_accordion(),
        spacing="4",
        align="center",
        width="100%",
    )
