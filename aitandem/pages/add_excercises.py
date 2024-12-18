"""Page for the teacher to add new exercises."""

import reflex as rx
from ..models import Exercise, Tag
from sqlmodel import select, or_

class ExerciseState(rx.State):
    exercises: list[Exercise] = []
    tag_list: list[Tag] = []
    tag_names: list[str] = [] # the tag.names as a str
    search_value: str = ""

    def search_exercises(self, search_value):
        """Search for a specific exercise."""
        self.search_value = search_value
        self.load_exercises()

    def load_exercises(self):
        """Get exercises from DB."""
        with rx.session() as session:
            # load exercises
            query_exercises = select(Exercise)
            # search for distinct entries
            if self.search_value:
                search_value = f"%{str(self.search_value).lower()}%"
                query_exercises = query_exercises.where(
                    or_(
                        *[
                            getattr(Exercise, field).ilike(search_value)
                            for field in Exercise.get_fields()
                        ],
                    )
                )
            self.exercises = session.exec(query_exercises).all()

    def load_tags(self):
        """Get tags from DB."""
        with rx.session() as session:
            # load tags
            query_tags = select(Tag)
            self.tag_list = session.exec(query_tags).all()
            self.tag_names = [tag.name for tag in self.tag_list]

    def submit_tag(self, form_data: dict):
        """add tags to DB."""
        with rx.session() as session:
            # check if tag is not None
            if form_data["tag"] == "":
                return rx.window_alert("Please enter a tag name.")

            # check if tag exists
            existing_tag = session.exec(select(Tag).where(Tag.name == form_data["tag"])).one_or_none()
            if existing_tag is not None:
                return rx.window_alert("Tag exists already.")

            new_tag = Tag(name=form_data["tag"])
            # add tag to db
            session.add(new_tag)
            session.commit()
            self.load_tags()

            return rx.toast.success(
                "Tag has been added and can now be selected.",
                duration=2500,
                position="bottom-center",
                invert=True,
            )

    def submit_exercise(self, form_data: dict):
        """add exercises to DB."""
        with rx.session() as session:
            # check if title is empty
            if not form_data["title"]:
                return rx.window_alert("Please enter a title for the exercise.")
            # create instance and fill its fields
            new_exercise = Exercise()
            new_exercise.title = form_data["title"]
            new_exercise.description = form_data["description"]
            new_exercise.tags = form_data["ex-tag"]
            # add exercises to db
            session.add(new_exercise)
            session.commit()
            # reload exercises
            self.load_exercises()

        return rx.toast.success(
            "Exercise has been added.",
            duration=2500,
            position="bottom-center",
            invert=True,
        )

def add_exercise_button() -> rx.Component:
    """button for adding new exercises."""
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
                            ExerciseState.tag_names,
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
                # load new tags
                on_mount=ExerciseState.load_tags,
                # submit new exercises
                on_submit=ExerciseState.submit_exercise,
                reset_on_submit=False,
            ),
            # add new tags
            tag_dialog(),
        ),
        unmount_on_exit=False
    )

def tag_dialog():
    """dialog for adding new tags."""
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button(
                "New tag",
            ),
        ),
        rx.dialog.content(
            rx.form(
                rx.text("Name", padding_bottom="0.5em"),
                rx.input(
                    placeholder="Enter new tag here",
                    name="tag",
                ),
                rx.center(
                    rx.dialog.close(
                        rx.button(
                            "Cancel",
                            color_scheme="red",
                        ),
                    ),
                    rx.form.submit(
                        rx.dialog.close(
                            rx.button("Add Tag",
                                      color_scheme="grass",
                                      type="submit",
                                      ),
                        ),
                    ),
                    padding_top="1em",
                    spacing="2",
                ),
                # submit new tags
                on_submit=ExerciseState.submit_tag,
            ),
        ),
    ),

def show_exercise(exercise: Exercise):
    """Show exercises on page in a table row."""
    return rx.table.row(
        rx.table.cell(exercise.id),
        rx.table.cell(exercise.title, max_width="175px"),
        rx.table.cell(exercise.description, max_width="400px"),
        rx.table.cell(exercise.tags, max_width="100px"),
        style={"_hover": {"bg": rx.color("gray", 3)}},
        align="center",
    )

def header_cell(text: str, icon: str):
    """create header cells."""
    return rx.table.column_header_cell(
        rx.hstack(
            rx.icon(icon, size=18),
            rx.text(text),
            align="center",
            spacing="3",
        ),
    )

def exercise_table():
    """the main table"""
    return rx.fragment(
        rx.flex(
            rx.box(
                # search bar
                rx.input(
                    rx.input.slot(rx.icon("search")),
                    placeholder="Search tasks...",
                    size="3",
                    max_width="250px",
                    style={"_hover": {"bg": rx.color("gray", 2)}},
                    on_change=lambda value: ExerciseState.search_exercises(value),
                ),
                flex="1",
            ),
            # the button for adding exercises
            rx.box(
                add_exercise_button(),
            ),
            width="100%",
        ),
        # head cells for the main table
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    header_cell("ID", "file-digit"),
                    header_cell("Task", "briefcase-business"),
                    header_cell("Description", "book-open-text"),
                    header_cell("Tag", "tag"),
                ),
            ),
            # dynamically render each new entry
            rx.table.body(rx.foreach(ExerciseState.exercises, show_exercise)),
            on_mount=ExerciseState.load_exercises(),
            variant="surface",
            size="3",
            width="85vw",
            overflow_y="auto",
            max_height="70vh",
        ),
    ),

@rx.page(route="/add-exercises")
def add_exercises_default() -> rx.Component:
    """add exercises page."""
    return rx.center(
        rx.color_mode.button(position="top-right", type="button"),
        rx.vstack(
            rx.center(
                rx.heading("Exercises", size="8", padding_top="2em"),
                padding_bottom="2em",
                width="100%",
            ),
            exercise_table(),
        ),
    )