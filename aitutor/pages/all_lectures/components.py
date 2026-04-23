"""Components for the all lectures page."""

import reflex as rx

from aitutor.language_state import LanguageState as LS
from aitutor.pages.all_lectures.state import AllLecturesState, LectureWithRole
from aitutor.pages.my_lectures.components import lecture_role_text


def lecture_row(lecture_with_role: LectureWithRole) -> rx.Component:
    """Render a single lecture row."""
    lecture = lecture_with_role[0]
    role = lecture_with_role[1]
    lecture_id = rx.cond(lecture.id != None, lecture.id, 0)  # noqa: E711

    return rx.fragment(
        rx.table.row(
            rx.table.cell(
                rx.hstack(
                    rx.icon_button(
                        rx.cond(
                            AllLecturesState.expanded_lecture_id == lecture_id,
                            rx.icon("chevron-down", size=16),
                            rx.icon("chevron-right", size=16),
                        ),
                        variant="ghost",
                        size="1",
                        on_click=AllLecturesState.toggle_lecture_details(lecture_id),
                        _hover={"cursor": "pointer"},
                    ),
                    rx.text(lecture.lecture_name),
                    align="center",
                    spacing="2",
                ),
            ),
            rx.table.cell(lecture_role_text(role)),
            rx.table.cell(
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
            ),
        ),
        rx.cond(
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
        ),
    )


def join_lecture_dialog() -> rx.Component:
    """Dialog for joining a lecture."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title(LS.join_lecture),
                rx.text(AllLecturesState.selected_lecture_name, weight="medium"),
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
                    rx.button(
                        LS.cancel,
                        variant="outline",
                        on_click=AllLecturesState.close_join_dialog,
                        _hover={"cursor": "pointer"},
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
    )


def all_lectures_table() -> rx.Component:
    """Render the searchable table of all lectures."""
    return rx.vstack(
        rx.hstack(
            rx.input(
                value=AllLecturesState.search_text,
                placeholder=LS.search_placeholder,
                on_change=AllLecturesState.update_search_text,
                width="22em",
                max_width="100%",
            ),
            width="85vw",
            max_width="100%",
        ),
        rx.cond(
            AllLecturesState.filtered_lectures,
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell(LS.lecture_name),
                        rx.table.column_header_cell(LS.role),
                        rx.table.column_header_cell(""),
                    )
                ),
                rx.table.body(
                    rx.foreach(AllLecturesState.filtered_lectures, lecture_row)
                ),
                variant="surface",
                size="3",
                width="85vw",
                max_width="100%",
                overflow_y="auto",
                max_height="66vh",
            ),
            rx.cond(
                AllLecturesState.lectures,
                rx.text(LS.no_matching_lectures, size="4"),
                rx.text(LS.no_joined_lectures, size="4"),
            ),
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