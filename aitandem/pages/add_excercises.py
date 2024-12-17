"""Page for the teacher to add new exercises."""

import reflex as rx

from ..models import Exercise


class ExerciseState(rx.State):
    exercises: list[Exercise] = []

    def submit_exercise(self, form_data: dict):
        with rx.session() as session:
            new_exercise = Exercise()
            new_exercise.title = form_data["title"]
            new_exercise.description = form_data["description"]
            new_exercise.tags = form_data["ex-tag"]
            session.add(new_exercise)
            session.commit()

        return rx.toast.success(
            "Exercise has been added.",
            duration=2500,
            position="bottom-center",
            invert=True,
        )


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
                        "New Exercise",
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
            rx.form(
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
                    type="text",
                    name="title",
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
                    type="text",
                    name="description",
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
                rx.hstack(
                    rx.box(
                        rx.select(
                            ["test"],
                            placeholder="Select a tag here",
                            name="ex-tag"
                        ),
                        flex="1",
                    ),
                    rx.box(
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
                                          type="submit",
                                          ),
                                as_child=True,
                            ),
                            padding_left="0.5em",
                            padding_bottom="0.5em",
                        ),
                    ),
                ),
                on_submit=ExerciseState.submit_exercise,
                reset_on_submit=False,
            ),
        ),
        unmount_on_exit=False
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


def exercise_table():
    return rx.fragment(
        rx.flex(
            rx.box(
                rx.input(
                    rx.input.slot(rx.icon("search")),
                    placeholder="Search tasks...",
                    size="3",
                    max_width="250px",
                    style={"_hover": {"bg": rx.color("gray", 2)}},

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
            rx.table.body(
                rx.table.row(
                    rx.table.cell("Test-task"),
                    rx.table.cell("This is just a test description"),
                    rx.table.cell("001"),
                ),
                style={"_hover": {"bg": rx.color("gray", 3)}},
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
            rx.center(
                rx.heading("Exercises", size="8"),
                padding_bottom="2em",
                width="100%",
            ),
            exercise_table(),
        ),
        height="40vh",
    )
