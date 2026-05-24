"""Reflex renderers for generated chat UI actions."""

import reflex as rx

from aitutor.pages.chat.generated_diagram_components import show_diagram_action
from aitutor.pages.chat.generated_ui import (
    GeneratedUiAction,
    GeneratedUiKind,
    QuizOption,
    QuizQuestion,
)


def quiz_option_button(
    question: QuizQuestion,
    message_index: int,
    action_index: int,
    question_index: int,
    option: QuizOption,
    option_index: int,
    on_select,
) -> rx.Component:
    """Render one selectable quiz option."""
    has_correct_answer = question.correct_option_index != None
    is_selected = question.selected_option_index == option_index
    is_correct = question.correct_option_index == option_index
    is_answered = question.selected_option_index != None

    return rx.button(
        rx.text(option.label, size="2", text_align="left", width="100%"),
        width="100%",
        justify="start",
        variant=rx.cond(is_selected, "solid", "soft"),
        color_scheme=rx.cond(
            is_selected & has_correct_answer,
            rx.cond(is_correct, "green", "red"),
            rx.cond(is_selected, "accent", "gray"),
        ),
        white_space="normal",
        height="auto",
        min_height="2.5em",
        padding="0.75em",
        disabled=is_answered,
        _hover=rx.cond(
            is_answered,
            {"cursor": "default"},
            {"cursor": "pointer"},
        ),
        on_click=on_select(message_index, action_index, question_index, option_index),
    )


def quiz_question(
    question: QuizQuestion,
    message_index: int,
    action_index: int,
    active_question_index: int,
    question_index: int,
    on_select,
) -> rx.Component:
    """Render one generated multiple-choice quiz question."""
    selected_index = question.selected_option_index
    has_correct_answer = question.correct_option_index != None
    is_correct = selected_index == question.correct_option_index

    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.badge(question_index + 1, variant="soft"),
                rx.text(question.question, weight="bold", size="3"),
                align="start",
                spacing="2",
            ),
            rx.vstack(
                rx.foreach(
                    question.options,
                    lambda option, option_index: quiz_option_button(
                        question,
                        message_index,
                        action_index,
                        question_index,
                        option,
                        option_index,
                        on_select,
                    ),
                ),
                spacing="2",
                width="100%",
            ),
            rx.cond(
                (selected_index != None) & (question.explanation != ""),
                rx.callout(
                    question.explanation,
                    icon=rx.cond(
                        has_correct_answer & is_correct,
                        "circle-check",
                        "info",
                    ),
                    color_scheme=rx.cond(
                        has_correct_answer & is_correct,
                        "green",
                        rx.cond(has_correct_answer, "red", "blue"),
                    ),
                    width="100%",
                ),
            ),
            spacing="3",
            align="stretch",
        ),
        padding_top="0.75em",
        padding_bottom="0.75em",
        width="100%",
        display=rx.cond(question_index == active_question_index, "block", "none"),
    )


def show_quiz_action(
    action: GeneratedUiAction,
    message_index: int,
    action_index: int,
    on_select,
) -> rx.Component:
    """Render a generated multiple-question quiz."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon("list-checks", size=18),
                rx.text(action.title, weight="bold", size="4"),
                align="center",
                spacing="2",
            ),
            rx.foreach(
                action.questions,
                lambda question, question_index: quiz_question(
                    question,
                    message_index,
                    action_index,
                    action.current_question_index,
                    question_index,
                    on_select,
                ),
            ),
            spacing="2",
            align="stretch",
        ),
        background_color=rx.color("gray", 2),
        border=f"1px solid {rx.color('gray', 6)}",
        border_radius="8px",
        padding="1em",
        margin_top="0.75em",
        max_width=["30em", "30em", "50em", "50em", "50em", "50em"],
        width="100%",
    )


def generated_ui_action(
    action: GeneratedUiAction,
    message_index: int,
    action_index: int,
    on_select,
) -> rx.Component:
    """Render one generated UI action from its typed contract."""
    return rx.cond(
        action.kind == GeneratedUiKind.SHOW_DIAGRAM,
        show_diagram_action(action),
        show_quiz_action(action, message_index, action_index, on_select),
    )


def generated_ui_actions(
    actions: list[GeneratedUiAction],
    message_index: int,
    on_select,
) -> rx.Component:
    """Render generated UI actions for a chat message."""
    return rx.foreach(
        actions,
        lambda action, action_index: generated_ui_action(
            action, message_index, action_index, on_select
        ),
    )
