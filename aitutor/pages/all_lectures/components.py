"""Components for the all lectures page."""

import reflex as rx

from aitutor import routes
from aitutor.language_state import LanguageState as LS
from aitutor.pages.all_lectures.state import (
    ALL_LECTURES_FIELD_MAX_LENGTHS,
    AllLecturesState,
    LectureWithRole,
)


def back_to_my_lectures_button() -> rx.Component:
    """Render the button for navigating back to my lectures."""
    return rx.button(
        rx.icon("arrow-left", size=20),
        LS.my_lectures,
        on_click=rx.redirect(routes.MY_LECTURES),
        _hover={"cursor": "pointer"},
    )


def page_header() -> rx.Component:
    """Render the all lectures page header."""
    return rx.vstack(
        back_to_my_lectures_button(),
        rx.heading(LS.all_lectures, size="5"),
        spacing="5",
        align="start",
        width="85vw",
        margin_top=rx.breakpoints(initial="0.5em", md="2em"),
    )


def join_lecture_dialog() -> rx.Component:
    """Dialog for joining a lecture."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title(LS.join_lecture),
                rx.text(
                    AllLecturesState.selected_lecture_name,
                    size="4",
                    weight="bold",
                ),
                rx.cond(
                    AllLecturesState.selected_lecture_lecturer_name,
                    rx.vstack(
                        rx.text(LS.lecture_lecturer, weight="medium"),
                        rx.text(AllLecturesState.selected_lecture_lecturer_name),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),
                ),
                rx.cond(
                    AllLecturesState.selected_lecture_requires_code,
                    rx.vstack(
                        rx.text(LS.enter_registration_code),
                        rx.input(
                            value=AllLecturesState.entered_registration_code,
                            placeholder=LS.registration_code_placeholder,
                            on_change=AllLecturesState.set_entered_registration_code,
                            width="100%",
                            max_length=ALL_LECTURES_FIELD_MAX_LENGTHS[
                                "registration_code"
                            ],
                        ),
                        width="100%",
                        align="start",
                        spacing="2",
                    ),
                    rx.text(LS.no_registration_code_required),
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            LS.cancel,
                            variant="outline",
                            on_click=AllLecturesState.close_join_dialog,
                            _hover={"cursor": "pointer"},
                        ),
                    ),
                    rx.button(
                        LS.join,
                        on_click=AllLecturesState.join_selected_lecture,
                        disabled=~AllLecturesState.can_join_selected_lecture,
                        _hover={"cursor": "pointer"},
                    ),
                    justify="end",
                    width="100%",
                ),
                spacing="4",
                align="start",
                width="100%",
            ),
        ),
        open=AllLecturesState.join_dialog_is_open,
        on_open_change=AllLecturesState.set_join_dialog_is_open,
    )


def lectures_toolbar() -> rx.Component:
    """Render the all lectures search toolbar."""
    return rx.box(
        rx.input(
            rx.input.slot(
                rx.icon("search", size=18, color=rx.color("gray", 10)),
            ),
            rx.cond(
                AllLecturesState.search_text != "",
                rx.input.slot(
                    rx.icon_button(
                        rx.icon("x", size=14),
                        variant="ghost",
                        color_scheme="gray",
                        size="2",
                        on_click=AllLecturesState.update_search_text(""),
                        _hover={"cursor": "pointer"},
                    ),
                ),
            ),
            value=AllLecturesState.search_text,
            placeholder=LS.search_placeholder,
            on_change=AllLecturesState.update_search_text,
            max_length=ALL_LECTURES_FIELD_MAX_LENGTHS["search_text"],
            size="3",
            variant="surface",
            width="100%",
        ),
        width="85vw",
        max_width="36em",
        margin_top=rx.breakpoints(initial="1em", md="2.5em"),
    )


def empty_lectures_message() -> rx.Component:
    """Distinguish between no matches and no available lectures."""
    return rx.cond(
        AllLecturesState.lectures,
        rx.text(LS.no_matching_lectures, size="4"),
        rx.text(LS.no_available_lectures, size="4"),
    )


def join_action_button(role, lecture_id) -> rx.Component:
    """Render a join button or already-joined badge."""
    return rx.cond(
        role,
        rx.badge(
            rx.icon("check", size=12),
            LS.already_joined,
            color_scheme="green",
            variant="surface",
            size="2",
        ),
        rx.button(
            rx.icon("user-plus", size=14),
            LS.join,
            size="2",
            on_click=AllLecturesState.open_join_dialog(lecture_id),  # type: ignore[arg-type]
            _hover={"cursor": "pointer"},
        ),
    )


def lecturer_subtitle(lecturer_name) -> rx.Component:
    """Render the lecturer label and name."""
    return rx.hstack(
        rx.icon("graduation-cap", size=15, color=rx.color("gray", 10)),
        rx.text(
            lecturer_name,
            size="2",
            color_scheme="gray",
        ),
        spacing="2",
        align="center",
    )


def lecture_details_body(information_text) -> rx.Component:
    """Render the syllabus/details markdown or fallback message."""
    return rx.cond(
        information_text,
        rx.markdown(information_text),
        rx.text(LS.no_lecture_details, size="2", color_scheme="gray"),
    )


def lecture_details_dialog() -> rx.Component:
    """Details modal dialog for desktop screens."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.dialog.title(
                        rx.heading(
                            AllLecturesState.detail_lecture_name,
                            size="5",
                            weight="bold",
                        ),
                        margin="0",
                    ),
                    rx.dialog.close(
                        rx.icon_button(
                            rx.icon("x", size=18),
                            variant="ghost",
                            color_scheme="gray",
                            _hover={"cursor": "pointer"},
                        ),
                    ),
                    justify="between",
                    align="center",
                    width="100%",
                ),
                rx.hstack(
                    lecturer_subtitle(AllLecturesState.detail_lecturer_name),
                    join_action_button(
                        AllLecturesState.detail_lecture_role,
                        AllLecturesState.detail_lecture_id,
                    ),
                    justify="between",
                    align="center",
                    width="100%",
                ),
                rx.divider(),
                rx.scroll_area(
                    rx.box(
                        lecture_details_body(AllLecturesState.detail_lecture_info),
                        padding_right="1.5em",
                        padding_bottom="1em",
                    ),
                    max_height="65vh",
                    type="auto",
                    scrollbars="vertical",
                ),
                spacing="5",
                align="start",
                width="100%",
            ),
            padding="2.5em",
            max_width="60em",
        ),
        open=AllLecturesState.details_dialog_is_open,
        on_open_change=AllLecturesState.set_details_dialog_is_open,
    )


def lecture_card(lecture_with_role: LectureWithRole) -> rx.Component:
    """Render a single lecture card with consistent layout across all screen sizes."""
    lecture = lecture_with_role[0]
    role = lecture_with_role[1]
    lecture_id = lecture.id

    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading(
                    lecture.lecture_name,
                    as_="h2",
                    size="5",
                    weight="bold",
                ),
                join_action_button(role, lecture_id),
                justify="between",
                align="start",
                width="100%",
                spacing="3",
            ),
            lecturer_subtitle(lecture.lecturer_name),
            rx.spacer(),
            rx.desktop_only(
                rx.button(
                    rx.icon("info", size=14),
                    LS.lecture_info,
                    variant="surface",
                    color_scheme="gray",
                    size="2",
                    on_click=AllLecturesState.open_details_dialog(lecture_id),  # type: ignore[arg-type]
                    _hover={"cursor": "pointer"},
                ),
            ),
            rx.mobile_and_tablet(
                rx.accordion.root(
                    rx.accordion.item(
                        header=rx.hstack(
                            rx.icon("info", size=14),
                            rx.text(LS.lecture_info, size="2"),
                            spacing="2",
                            align="center",
                        ),
                        content=rx.box(
                            rx.divider(),
                            rx.box(
                                lecture_details_body(lecture.lecture_information_text),
                                padding_y="0.75em",
                            ),
                            width="100%",
                        ),
                    ),
                    collapsible=True,
                    variant="ghost",
                    width="100%",
                ),
            ),
            spacing="3",
            align="start",
            width="100%",
            height="100%",
        ),
        padding="1.5em",
        _hover={
            "box_shadow": "var(--shadow-2)",
        },
    )


def lectures_cards_list() -> rx.Component:
    """Render the grid of lecture cards."""
    return rx.grid(
        rx.foreach(AllLecturesState.filtered_lectures, lecture_card),
        grid_template_columns="repeat(auto-fill, minmax(min(100%, 28em), 1fr))",
        gap="1.5em",
        width="85vw",
        padding_y="2em",
    )


def lectures_cards() -> rx.Component:
    """Render the searchable cards of all lectures."""
    return rx.vstack(
        lectures_toolbar(),
        rx.cond(
            AllLecturesState.filtered_lectures,
            lectures_cards_list(),
            empty_lectures_message(),
        ),
        spacing="3",
        align="center",
        width="100%",
    )


def all_lectures_content() -> rx.Component:
    """Main content for the all lectures page."""
    return rx.vstack(
        rx.html("<style>body { pointer-events: auto !important; }</style>"),
        page_header(),
        lectures_cards(),
        join_lecture_dialog(),
        lecture_details_dialog(),
        spacing="3",
        align="center",
    )
