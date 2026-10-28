"""Tag components shared by the classic and the Level AI exercise forms.

This module provides:
- new_tag_dialog: dialog for creating a new lecture tag
- tag_selection: menu for selecting lecture tags plus the selected tag badges

The components only render; each form passes the state vars and event handlers of
its own state.
"""

import reflex as rx
from reflex.event import EventCallback

from aitutor.language_state import LanguageState
from aitutor.pages.lecture_manage_exercises.state import (
    LECTURE_MANAGE_EXERCISES_FIELD_MAX_LENGTHS,
)


def new_tag_dialog(
    *,
    tag_name: str | rx.Var[str],
    on_tag_name_change: EventCallback[str],
    on_add: EventCallback[()],
    is_open: bool | rx.Var[bool],
    on_open_change: EventCallback[bool],
) -> rx.Component:
    """Dialog for adding a new lecture tag.

    Args:
        tag_name: The name currently entered in the dialog.
        on_tag_name_change: Handler receiving the entered name.
        on_add: Handler that creates the tag (also triggered by Enter).
        is_open: Whether the dialog is open.
        on_open_change: Handler receiving the new open state.
    """
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button(
                rx.hstack(
                    rx.icon("plus", size=20),
                    rx.icon("tag", size=20),
                    align="center",
                    spacing="1",
                ),
                LanguageState.new_tag,
                type="button",
                _hover={"cursor": "pointer"},
            ),
        ),
        rx.dialog.content(
            rx.vstack(
                rx.heading(LanguageState.new_tag),
                rx.input(
                    placeholder=LanguageState.tagname,
                    value=tag_name,
                    on_change=on_tag_name_change,
                    width="100%",
                    on_key_down=lambda key: rx.cond(key == "Enter", on_add, None),
                    max_length=LECTURE_MANAGE_EXERCISES_FIELD_MAX_LENGTHS["tag_name"],
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            rx.text(LanguageState.cancel),
                            variant="outline",
                            type="button",
                            _hover={"cursor": "pointer"},
                        ),
                    ),
                    rx.button(
                        LanguageState.add_tag,
                        on_click=on_add,
                        type="button",
                        _hover=rx.cond(
                            tag_name == "",
                            {"cursor": "not-allowed"},
                            {"cursor": "pointer"},
                        ),
                        disabled=tag_name == "",
                    ),
                    padding_top="1em",
                    spacing="2",
                    justify="end",
                    width="100%",
                ),
            ),
            width="20em",
            max_width="90vw",
        ),
        open=is_open,
        on_open_change=on_open_change,
    )


def tag_selection(
    *,
    selectable_tags: list[str] | rx.Var[list[str]],
    selected_tags: list[str] | rx.Var[list[str]],
    on_select: EventCallback[str],
    on_remove: EventCallback[str],
    add_tag_dialog: rx.Component,
) -> rx.Component:
    """Menu for selecting lecture tags, followed by the selected tags as badges.

    Args:
        selectable_tags: Lecture tags that are not selected yet.
        selected_tags: Tags selected for the exercise.
        on_select: Handler receiving the tag name to select.
        on_remove: Handler receiving the tag name to remove.
        add_tag_dialog: Dialog for creating a new tag, shown next to the menu.
    """
    return rx.vstack(
        rx.text(
            LanguageState.tags + ":",
            size="3",
            weight="medium",
            text_align="left",
            width="100%",
            padding_top="1.5em",
            padding_bottom="0.5em",
        ),
        rx.hstack(
            rx.menu.root(
                rx.menu.trigger(
                    rx.button(
                        rx.icon("list", size=18),
                        LanguageState.select_tags,
                        type="button",
                        _hover={"cursor": "pointer"},
                    ),
                ),
                rx.menu.content(
                    rx.foreach(
                        selectable_tags,
                        lambda tag_name: rx.menu.item(
                            tag_name,
                            on_click=on_select(tag_name),
                        ),
                    ),
                    min_width="10em",
                ),
            ),
            add_tag_dialog,
            align="center",
            justify="between",
            width="100%",
        ),
        rx.hstack(
            rx.foreach(
                selected_tags,
                lambda tag: rx.badge(
                    rx.hstack(
                        rx.text(tag),
                        rx.icon("circle-x", size=16),
                        spacing="1",
                        align_items="center",
                    ),
                    on_click=on_remove(tag),
                    cursor="pointer",
                    size="3",
                    style={
                        "_hover": {
                            "background_color": "red",
                            "color": "black",
                        }
                    },
                ),
            ),
            margin_top="0.5em",
            margin_bottom="0.5em",
            wrap="wrap",
        ),
        spacing="1",
    )
