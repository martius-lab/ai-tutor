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
            ),
            rx.text_area(
                placeholder="describe the task here",
                size="3",
                width="100%",
                height="150px",
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
                        rx.button("Add Task"),
                        style={"background-color": "green", "color": "white"},
                    ),
                ),
                padding_top="1.5em",
                spacing="3",
                justify="end",
            ),
        ),
    )


@rx.page(route="/add-exercises")
def add_exercises_default() -> rx.Component:
    """add exercises page."""
    return rx.center(
        add_exercise_button(),
        height="100vh",
    )
