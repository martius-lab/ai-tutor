"""Page for the teacher to add new exercises."""

import reflex as rx


def add_exercise_button() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button(
                rx.icon("file-plus", size=26),
                rx.text("Add Exercise", size="4"),
                size="3",
            ),
        ),
        rx.dialog.content(
            rx.hstack(
                rx.badge(
                    rx.icon(tag="file-plus", size=34),
                    color_scheme="grass",
                    radius="full",
                ),
                rx.vstack(
                    rx.dialog.title(
                        "Add New Exercise",
                        weight="bold",
                        margin="0",
                    ),
                    rx.dialog.description(
                        "add a new exercise for the students",
                    ),
                    spacing="1",
                    height="100%",
                    align_items="start",
                    justify_content="start",
                ),
                height="100%",
                spacing="4",
                margin_bottom="1.5em",
                align_items="start",
                width="100%",
            ),
            rx.text(
                "Title: ",
                size="3",
                weight="medium",
                text_align="left",
                width="100%",
                padding_bottom="0.5em",
            ),
            rx.input(
                placeholder="exercise title",
                size="3",
                width="100%",
            ),
            rx.text(
                "Description: ",
                size="3",
                weight="medium",
                text_align="left",
                width="100%",
                padding_top="1.5em",
                padding_bottom="0.5em",
            ),
            rx.text_area(
                placeholder="describe the task here",
                size="3",
                width="100%",
                height="150px",
            ),
            rx.text(
                "Tag: ",
                size="3",
                weight="medium",
                text_align="left",
                width="100%",
                padding_top="1.5em",
                padding_bottom="0.5em",
            ),
            rx.input(
                placeholder="set the tag for this task",
                size="3",
                width="100%",
            ),
            rx.flex(
                rx.dialog.close(
                    rx.button(
                        "Cancel",
                        color_scheme="gray",
                    ),
                ),
                rx.form.submit(
                    rx.dialog.close(
                        rx.button("Add Task",
                                  color_scheme="grass",
                                  ),
                    ),
                ),
                padding_top="1.5em",
                spacing="3",
                justify="end",
            ),
        ),
        unmount_on_exit=False,
    )


def header_cell(text: str, icon: str):
    return rx.table.column_header_cell(
        rx.hstack(
            rx.icon(icon, size=18),
            rx.text(text),
            align="center",
            spacing="3",
        ),
    )


def head_element():
    return rx.fragment(
        rx.flex(
            rx.box(
                rx.input(
                    rx.input.slot(rx.icon("search")),
                    placeholder="Search tasks...",
                    size="3",
                    max_width="250px",
                ),
                flex="1",
            ),
            rx.box(
                add_exercise_button(),
            ),
            width="100%",
        ),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    header_cell("Task", "briefcase-business"),
                    header_cell("Description", "book-open-text"),
                    header_cell("Tag", "tag"),
                ),
            ),
            variant="surface",
            size="3",
            width="85vw",
        ),
    )



@rx.page(route="/add-exercises")
def add_exercises_default() -> rx.Component:
    """add exercises page."""
    return rx.center(
        rx.color_mode.button(position="top-right", type="button"),
        rx.vstack(
            head_element(),
        ),
        height="40vh",
    )
