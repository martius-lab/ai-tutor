"""Components for the lecture overview page."""

import reflex as rx

from aitutor import DisplayConfigState, routes
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
    """Render dashboard shell with explicit placeholder data for lecture exercises."""
    return rx.card(
        rx.vstack(
            rx.heading(f"{LectureOverviewState.lecture_name} {LS.dashboard}"),
            rx.text(LS.welcome_back, weight="medium"),
            rx.progress(
                value=100,
                max=100,
                width="100%",
            ),
            rx.callout(
                "Placeholder data: lecture-specific exercises are not connected yet.",
                icon="info",
                width="100%",
            ),
            rx.hstack(
                rx.icon("circle-check", size=20),
                rx.text("0/0 lecture-specific exercises submitted (placeholder)."),
                align="center",
            ),
            rx.hstack(
                rx.text(LS.next_deadline, weight="bold"),
                rx.text("No lecture-specific deadline available yet (placeholder)."),
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
    """Render the overview information accordion.

    This is copied from the home page structure for now. The lecture information panel
    uses the selected lecture's text instead of the global lecture information text.
    """
    privacy_notice_short: str = get_privacy_notice_short()
    return rx.cond(
        (DisplayConfigState.how_to_use_text != "")
        | (DisplayConfigState.general_information_text != "")
        | (LectureOverviewState.lecture_information_text != "")
        | (privacy_notice_short != ""),
        rx.accordion.root(
            rx.accordion.item(
                header=LS.lecture_info,
                content=lecture_information_content(),
            ),
            rx.cond(
                DisplayConfigState.how_to_use_text != "",
                rx.accordion.item(
                    header=LS.how_to_use_aitutor,
                    content=rx.markdown(DisplayConfigState.how_to_use_text),
                ),
            ),
            rx.cond(
                DisplayConfigState.general_information_text != "",
                rx.accordion.item(
                    header=LS.general_info,
                    content=rx.markdown(DisplayConfigState.general_information_text),
                ),
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
        lecture_dashboard_card(),
        lecture_info_accordion(),
        lecture_legal_info_links(),
        spacing="4",
        align="center",
        width="100%",
    )