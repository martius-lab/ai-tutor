"""Components for the all lectures page."""

import reflex as rx

from aitutor.language_state import LanguageState as LS
from aitutor.pages.all_lectures.state import AllLecturesState, LectureWithRole


def lecture_details_toggle_button(lecture_id) -> rx.Component:
    """Render the button for expanding or collapsing lecture details."""
    return rx.icon_button(
        rx.cond(
            AllLecturesState.expanded_lecture_id == lecture_id,
            rx.icon("chevron-down", size=16),
            rx.icon("chevron-right", size=16),
        ),
        variant="ghost",
        size="1",
        on_click=AllLecturesState.toggle_lecture_details(lecture_id),
        _hover={"cursor": "pointer"},
    )


def lecture_name_cell(lecture, lecture_id) -> rx.Component:
    """Render the lecture name cell with its details toggle."""
    return rx.table.cell(
        rx.hstack(
            lecture_details_toggle_button(lecture_id),
            rx.text(lecture.lecture_name),
            align="center",
            spacing="2",
        ),
    )


def lecturer_cell(lecture) -> rx.Component:
    """Render the lecturer information cell."""
    return rx.table.cell(
        rx.cond(
            lecture.lecturer_name,
            lecture.lecturer_name,
            LS.no_lecturer_information,
        )
    )


def join_status_cell(role: int | None, lecture_id) -> rx.Component:
    """Render the join action or joined status for a lecture."""
    return rx.table.cell(
        rx.cond(
            role == None,  # noqa: E711
            rx.button(
                LS.join,
                size="2",
                on_click=AllLecturesState.open_join_dialog(lecture_id),
                _hover={"cursor": "pointer"},
            ),
            rx.text(LS.already_joined),
        )
    )


def lecture_details_row(lecture, lecture_id) -> rx.Component:
    """Render the expanded lecture details row when selected."""
    return rx.cond(
        AllLecturesState.expanded_lecture_id == lecture_id,
        rx.table.row(
            rx.table.cell(
                rx.cond(
                    lecture.lecture_information_text,
                    rx.markdown(lecture.lecture_information_text),
                    rx.text(LS.no_lecture_details),
                ),
                col_span=3,
            )
        ),
    )


def lecture_row(lecture_with_role: LectureWithRole) -> rx.Component:
    """Render a single lecture row."""
    lecture = lecture_with_role[0]
    role = lecture_with_role[1]
    lecture_id = rx.cond(lecture.id != None, lecture.id, 0)  # noqa: E711

    return rx.fragment(
        rx.table.row(
            lecture_name_cell(lecture, lecture_id),
            lecturer_cell(lecture),
            join_status_cell(role, lecture_id),
        ),
        lecture_details_row(lecture, lecture_id),
    )


def join_lecture_dialog() -> rx.Component:
    """Dialog for joining a lecture."""
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.vstack(
                rx.alert_dialog.title(LS.join_lecture),
                rx.text(
                    AllLecturesState.selected_lecture_name,
                    size="4",
                    weight="bold",
                    line_height="1.3",
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
                        ),
                        width="100%",
                        align="start",
                        spacing="2",
                    ),
                    rx.text(LS.no_registration_code_required),
                ),
                rx.hstack(
                    rx.alert_dialog.cancel(
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
    return rx.hstack(
        rx.input(
            value=AllLecturesState.search_text,
            placeholder=LS.search_placeholder,
            on_change=AllLecturesState.update_search_text,
            width="22em",
            max_width="100%",
        ),
        width="85vw",
        max_width="100%",
    )


def lectures_table() -> rx.Component:
    """Render the table containing all currently filtered lectures."""
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell(LS.lecture_name),
                rx.table.column_header_cell(LS.lecture_lecturer),
                rx.table.column_header_cell(""),
            )
        ),
        rx.table.body(rx.foreach(AllLecturesState.filtered_lectures, lecture_row)),
        variant="surface",
        size="3",
        width="85vw",
        max_width="100%",
        overflow_y="auto",
        max_height="66vh",
    )


def empty_lectures_message() -> rx.Component:
    """Render the appropriate empty state for the all lectures table."""
    return rx.cond(
        AllLecturesState.lectures,
        rx.text(LS.no_matching_lectures, size="4"),
        rx.text(LS.no_available_lectures, size="4"),
    )


def all_lectures_table() -> rx.Component:
    """Render the searchable table of all lectures."""
    return rx.vstack(
        lectures_toolbar(),
        rx.cond(
            AllLecturesState.filtered_lectures,
            lectures_table(),
            empty_lectures_message(),
        ),
        spacing="3",
        align="center",
        width="100%",
    )


def all_lectures_content() -> rx.Component:
    """Main content for the all lectures page."""
    return rx.vstack(
        all_lectures_table(),
        join_lecture_dialog(),
        spacing="3",
        align="center",
        width="100%",
    )
