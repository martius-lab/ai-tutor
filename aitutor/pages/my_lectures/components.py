"""Components for the my lectures page."""

import reflex as rx

import aitutor.routes as routes
from aitutor.components.dialogs import destructive_confirm
from aitutor.language_state import LanguageState as LS
from aitutor.models import Lecture, LectureRole
from aitutor.pages.my_lectures.state import (
    ROLE_FILTER_ALL,
    ROLE_FILTER_NOT_JOINED,
    ROLE_FILTER_OWNER,
    ROLE_FILTER_STUDENT,
    ROLE_FILTER_TUTOR,
    LectureWithRole,
    MyLecturesState,
)


def lecture_role_text(role: int | None):
    """Convert a LectureRole to text in a way that works for Reflex."""
    return rx.match(
        role,
        (LectureRole.OWNER.value, LS.owner_role),
        (LectureRole.TUTOR.value, LS.tutor_role),
        (LectureRole.STUDENT.value, LS.student_role),
        LS.not_joined,
    )


def role_filter_button(label, value: str) -> rx.Component:
    """Render a small role filter button."""
    return rx.button(
        label,
        variant=rx.cond(MyLecturesState.role_filter == value, "solid", "outline"),  # type: ignore
        size="2",
        on_click=MyLecturesState.set_role_filter(value),
        _hover={"cursor": "pointer"},
    )


def role_filter_select() -> rx.Component:
    """Render the role filter as a compact dropdown menu."""
    return rx.menu.root(
        rx.menu.trigger(
            rx.button(
                role_filter_label(),
                rx.icon("chevron-down", size=16),
                variant="outline",
                width="12em",
                max_width="100%",
                justify_content="space-between",
                _hover={"cursor": "pointer"},
            ),
        ),
        rx.menu.content(
            rx.menu.item(
                LS.all,
                on_click=MyLecturesState.set_role_filter(ROLE_FILTER_ALL),
            ),
            rx.menu.item(
                LS.owner_role,
                on_click=MyLecturesState.set_role_filter(ROLE_FILTER_OWNER),
            ),
            rx.menu.item(
                LS.tutor_role,
                on_click=MyLecturesState.set_role_filter(ROLE_FILTER_TUTOR),
            ),
            rx.menu.item(
                LS.student_role,
                on_click=MyLecturesState.set_role_filter(ROLE_FILTER_STUDENT),
            ),
            rx.cond(
                MyLecturesState.is_global_admin,
                rx.menu.item(
                    LS.not_joined,
                    on_click=MyLecturesState.set_role_filter(ROLE_FILTER_NOT_JOINED),
                ),
            ),
        ),
    )


def role_filter_label():
    """Return the localized label for the active role filter."""
    return rx.match(
        MyLecturesState.role_filter,
        (ROLE_FILTER_OWNER, LS.owner_role),
        (ROLE_FILTER_TUTOR, LS.tutor_role),
        (ROLE_FILTER_STUDENT, LS.student_role),
        (ROLE_FILTER_NOT_JOINED, LS.not_joined),
        LS.all,
    )


def role_filter_text(label, value) -> rx.Component:
    """Render clickable role text without badge styling."""
    return rx.text(
        label,
        on_click=MyLecturesState.set_role_filter(value),
        _hover={"cursor": "pointer"},
    )


def role_filter_value(role: int | None):
    """Return the filter value for a role."""
    return rx.match(
        role,
        (LectureRole.OWNER.value, ROLE_FILTER_OWNER),
        (LectureRole.TUTOR.value, ROLE_FILTER_TUTOR),
        (LectureRole.STUDENT.value, ROLE_FILTER_STUDENT),
        ROLE_FILTER_NOT_JOINED,
    )


def add_lecture_button() -> rx.Component:
    """Button for creating a new lecture."""
    return rx.cond(
        MyLecturesState.can_create_lectures,
        rx.link(
            rx.button(
                rx.flex(rx.icon("plus", size=15), LS.add, gap="0.5em", align="center"),
                _hover={"cursor": "pointer"},
            ),
            href=routes.EDIT_LECTURE + "/new",
        ),
    )


def browse_lectures_button() -> rx.Component:
    """Button for navigating to all lectures."""
    return rx.link(
        rx.button(
            rx.flex(
                rx.icon("book", size=15), LS.join_lecture, gap="0.5em", align="center"
            ),
            variant="outline",
            _hover={"cursor": "pointer"},
        ),
        href=routes.ALL_LECTURES,
    )


def leave_lecture_button(lecture: Lecture, *, width: str | None = None) -> rx.Component:
    """Render the leave lecture button with a destructive confirmation dialog."""
    assert lecture.id is not None, "Lecture must be persisted to render leave button."
    return destructive_confirm(
        title=LS.leave_lecture + ": " + lecture.lecture_name,
        description=LS.leave_lecture_description,
        confirm_text=LS.leave_lecture,
        cancel_text=LS.cancel,
        on_confirm=MyLecturesState.leave_lecture(lecture.id),
        trigger=rx.button(
            rx.flex(
                rx.icon("log-out", size=15),
                LS.leave_lecture,
                gap="0.5em",
                align="center",
            ),
            color_scheme="red",
            variant="outline",
            width=width,
            _hover={"cursor": "pointer"},
        ),
    )


def enter_lecture_button(lecture: Lecture, *, width: str | None = None) -> rx.Component:
    """Render the button for entering a lecture."""
    assert lecture.id is not None, "Lecture must be persisted to render enter button."
    return rx.link(
        rx.button(
            rx.flex(
                rx.icon("log-in", size=15),
                LS.enter,
                gap="0.5em",
                align="center",
            ),
            width=width,
            _hover={"cursor": "pointer"},
        ),
        href=f"{routes.LECTURE_OVERVIEW}/{lecture.id}",
        width=width,
    )


def edit_lecture_button(lecture: Lecture, *, width: str | None = None) -> rx.Component:
    """Render the button for editing a lecture."""
    assert lecture.id is not None, "Lecture must be persisted to render edit button."
    return rx.link(
        rx.button(
            rx.flex(
                rx.icon("pen", size=15),
                LS.edit,
                gap="0.5em",
                align="center",
            ),
            width=width,
            _hover={"cursor": "pointer"},
        ),
        href=f"{routes.EDIT_LECTURE}/{lecture.id}",
        width=width,
    )


def lecture_role_filter_text(role: int | None) -> rx.Component:
    """Render the clickable role label that also applies the role filter."""
    return role_filter_text(
        lecture_role_text(role),
        role_filter_value(role),
    )


def lecture_action_buttons(
    lecture: Lecture,
    role: int | None,
    *,
    full_width: bool = False,
) -> rx.Component:
    """Render the shared enter/edit/leave actions for one lecture."""
    button_width = "100%" if full_width else None

    return rx.hstack(
        enter_lecture_button(lecture, width=button_width),
        rx.cond(
            (role == LectureRole.OWNER.value) | MyLecturesState.is_global_admin,
            edit_lecture_button(lecture, width=button_width),
        ),
        rx.cond(
            role is not None,
            leave_lecture_button(lecture, width=button_width),
        ),
        spacing="2",
        wrap="wrap",
        width=button_width,
    )


def lectures_toolbar() -> rx.Component:
    """Render the toolbar with search, role filters and the add button."""
    search_input = rx.input(
        value=MyLecturesState.search_text,
        placeholder=LS.search_placeholder,
        on_change=MyLecturesState.update_search_text,
        width="22em",
        max_width="100%",
    )
    action_buttons = rx.hstack(
        rx.box(browse_lectures_button(), flex_shrink="0"),
        rx.cond(
            MyLecturesState.can_create_lectures,
            rx.box(add_lecture_button(), flex_shrink="0"),
        ),
        spacing="2",
        wrap="wrap",
    )

    return rx.center(
        rx.box(
            rx.desktop_only(
                rx.hstack(
                    rx.hstack(
                        search_input,
                        role_filter_select(),
                        wrap="wrap",
                        flex="1",
                        min_width="0",
                    ),
                    action_buttons,
                    justify="between",
                    align="center",
                    gap="1rem",
                    width="100%",
                ),
            ),
            rx.mobile_and_tablet(
                rx.vstack(
                    rx.input(
                        value=MyLecturesState.search_text,
                        placeholder=LS.search_placeholder,
                        on_change=MyLecturesState.update_search_text,
                        width="100%",
                    ),
                    rx.box(role_filter_select(), width="100%"),
                    action_buttons,
                    align="stretch",
                    spacing="3",
                    width="100%",
                ),
            ),
            width="85vw",
            max_width="100%",
        ),
        width="100%",
    )


def lecture_row(joined_lecture: LectureWithRole) -> rx.Component:
    """Render a single joined lecture row."""
    lecture: Lecture = joined_lecture[0]
    role = joined_lecture[1]

    return rx.table.row(
        rx.table.cell(lecture.lecture_name),
        rx.table.cell(lecture_role_filter_text(role)),
        rx.table.cell(lecture_action_buttons(lecture, role)),
    )


def lecture_card(joined_lecture: LectureWithRole) -> rx.Component:
    """Render a joined lecture as a mobile-friendly card."""
    lecture: Lecture = joined_lecture[0]
    role = joined_lecture[1]

    return rx.card(
        rx.vstack(
            rx.text(lecture.lecture_name, weight="bold", size="4", width="100%"),
            rx.hstack(
                rx.text(LS.role + ":", weight="medium"),
                lecture_role_filter_text(role),
                wrap="wrap",
                width="100%",
            ),
            lecture_action_buttons(lecture, role, full_width=True),
            spacing="3",
            align="start",
            width="100%",
        ),
        width="85vw",
        max_width="100%",
    )


def lectures_table() -> rx.Component:
    """Render the desktop lectures table."""
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell(LS.lecture_name),
                rx.table.column_header_cell(LS.role),
                rx.table.column_header_cell(""),
            )
        ),
        rx.table.body(rx.foreach(MyLecturesState.filtered_lectures, lecture_row)),
        variant="surface",
        size="3",
        width="85vw",
        max_width="100%",
        overflow_y="auto",
        max_height="66vh",
    )


def lecture_cards() -> rx.Component:
    """Render the mobile/tablet lectures card list."""
    return rx.vstack(
        rx.foreach(MyLecturesState.filtered_lectures, lecture_card),
        spacing="3",
        align="center",
        width="85vw",
        max_width="100%",
    )


def empty_lectures_message() -> rx.Component:
    """Render the empty state for the lectures list."""
    return rx.center(
        rx.cond(
            MyLecturesState.joined_lectures,
            rx.text(LS.no_matching_lectures, size="4"),
            rx.text(LS.no_joined_lectures, size="4"),
        ),
        width="85vw",
        max_width="100%",
    )


def my_lectures_table() -> rx.Component:
    """Table of all lectures joined by the current user."""
    return rx.vstack(
        lectures_toolbar(),
        rx.cond(
            MyLecturesState.filtered_lectures,
            rx.center(
                rx.box(
                    rx.desktop_only(lectures_table()),
                    rx.mobile_and_tablet(lecture_cards()),
                    width="85vw",
                    max_width="100%",
                ),
                width="100%",
            ),
            empty_lectures_message(),
        ),
        spacing="3",
        align="center",
        width="100%",
    )


def my_lectures_content() -> rx.Component:
    """Main content for the my lectures page."""
    return rx.vstack(
        rx.heading(LS.my_lectures, size="5", width="85vw", max_width="100%"),
        my_lectures_table(),
        spacing="3",
        align="center",
        width="100%",
    )
