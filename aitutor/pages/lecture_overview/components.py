"""Components for the lecture overview page."""

import reflex as rx

import aitutor.global_vars as gv
from aitutor import routes
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
    exercises_num = LectureOverviewState.exercises_with_result.length()  # type: ignore

    return rx.card(
        rx.vstack(
            rx.heading(f"{LectureOverviewState.lecture_name} {LS.dashboard}"),
            rx.text(LS.welcome_back, weight="medium"),
            rx.progress(
                value=LectureOverviewState.progress_value,  # type: ignore
                max=100,
                width="100%",
            ),
            rx.hstack(
                rx.icon("circle-check", color=gv.GREEN_CHECK_COLOR, size=20),
                rx.cond(
                    exercises_num > 0,
                    rx.text(
                        f"{LectureOverviewState.completed_exercises_num} \
                        /{exercises_num} \
                            {LS.open_exercises_submitted}"
                    ),
                    rx.text(LS.no_pending_exercises),
                ),
                align="center",
            ),
            rx.hstack(
                rx.text(LS.next_deadline, weight="bold"),
                rx.cond(
                    LectureOverviewState.next_deadline_task,
                    rx.text(LectureOverviewState.next_deadline_task),
                    rx.text(LS.no_upcoming_deadlines),
                ),
            ),
            spacing="4",
            align="start",
            width="100%",
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


def lecture_legal_info_links() -> rx.Component:
    """Render Impressum and privacy notice links."""
    return rx.hstack(
        rx.link(LS.impressum, href=routes.IMPRESSUM),
        rx.link(LS.privacy_notice, href=routes.PRIVACY_NOTICE),
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
        lecture_legal_info_links(),
        spacing="4",
        align="center",
        width="100%",
    )
