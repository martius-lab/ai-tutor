"""This module contains the chat component."""

import reflex as rx

import aitutor.routes as routes
from aitutor.models import UserRole
from aitutor.pages.chat.state import ChatState
from aitutor.pages.chat.state import ChatMessage
from aitutor.pages.navbar import with_navbar
from aitutor.auth.protection import require_role_at_least


def message_box(chat_message: ChatMessage) -> rx.Component:
    """Each message from the chat history gets its bounding box. Depending on the sender
    the message is aligned to the left for the LLM and aligned to the right for the
    user.
    """
    check_result_color = rx.cond(
        chat_message.check_passed,
        "green",
        "yellow",
    )
    return rx.box(
        rx.box(
            rx.markdown(
                chat_message.message,
                background_color=rx.cond(
                    chat_message.is_check_result,
                    rx.color(check_result_color, 4),
                    rx.cond(
                        chat_message.is_llm, rx.color("mauve", 4), rx.color("iris", 4)
                    ),
                ),
                color=rx.cond(
                    chat_message.is_check_result,
                    rx.color(check_result_color, 12),
                    rx.cond(
                        chat_message.is_llm, rx.color("mauve", 12), rx.color("iris", 12)
                    ),
                ),
                display="inline-block",
                padding="1em",
                border_radius="8px",
                max_width=["30em", "30em", "50em", "50em", "50em", "50em"],
            ),
            text_align=rx.cond(
                chat_message.is_check_result,
                "left",
                rx.cond(chat_message.is_llm, "left", "right"),
            ),
            margin_top="1em",
        ),
        width="100%",
    )


def chat_form() -> rx.Component:
    """
    Render the chat form for user input. Includes button to send Reply and button to
    check the conversation.
    """
    return rx.form(
        rx.vstack(
            rx.text_area(
                name="user_response",
                placeholder="Your Answer",
                required=True,
                width="100%",
                color_scheme="iris",
                enter_key_submit=True,
            ),
            rx.hstack(
                rx.hstack(
                    reset_conversation_button(),
                    check_conversation_button(),
                ),
                send_message_button(),
                width="100%",
                justify="between",
            ),
        ),
        on_submit=ChatState.send_message,
        reset_on_submit=True,
    )


def send_message_button() -> rx.Component:
    """
    Render the button to send a message.
    """
    return rx.button(
        rx.icon("send-horizontal", size=20),
        type="submit",
        color_scheme="iris",
        _hover=rx.cond(
            ChatState.waiting_for_response,
            {"cursor": "not-allowed"},
            {"cursor": "pointer"},
        ),
        loading=ChatState.waiting_for_response,
    )


def reset_conversation_button() -> rx.Component:
    """
    Render the button to reset the conversation.
    """
    return (
        rx.alert_dialog.root(
            rx.alert_dialog.trigger(
                rx.button(
                    "Reset Conversation",
                    color_scheme="red",
                    _hover=rx.cond(
                        ChatState.messages.length() < 2,  # type: ignore
                        {"cursor": "not-allowed"},
                        {"cursor": "pointer"},
                    ),
                    disabled=rx.cond(
                        ChatState.messages.length() < 2,  # type: ignore
                        True,
                        False,
                    ),
                )
            ),
            rx.alert_dialog.content(
                rx.alert_dialog.title("Reset Conversation"),
                rx.alert_dialog.description(
                    rx.cond(
                        ChatState.conversation_is_submitted,
                        "Are you sure you want to reset the conversation? "
                        + "(This will not delete your submission.)",
                        "Are you sure you want to reset the conversation? ",
                    )
                ),
                rx.hstack(
                    rx.alert_dialog.cancel(
                        rx.button(
                            "Cancel",
                            color_scheme="red",
                            _hover={"cursor": "pointer"},
                        ),
                    ),
                    rx.alert_dialog.action(
                        rx.button(
                            "Confirm",
                            color_scheme="iris",
                            on_click=ChatState.reset_conversation,
                            _hover={"cursor": "pointer"},
                        ),
                    ),
                    margin_top="1em",
                ),
            ),
        ),
    )


def check_conversation_button() -> rx.Component:
    """
    Render the button to check the conversation.
    """
    return rx.cond(
        ChatState.check_passed,
        rx.button(
            "Submit",
            color_scheme="green",
            type="button",
            _hover={"cursor": "pointer"},
            on_click=ChatState.submit_conversation,
        ),
        rx.cond(
            ChatState.check_is_loading,
            rx.button(
                "Check Conversation",
                color_scheme="yellow",
                type="button",
                _hover={"cursor": "not-allowed"},
                loading=True,
            ),
            rx.alert_dialog.root(
                rx.alert_dialog.trigger(
                    rx.button(
                        "Check Conversation",
                        color_scheme="yellow",
                        type="button",
                        _hover=rx.cond(
                            ChatState.messages.length() < 2,  # type: ignore
                            {"cursor": "not-allowed"},
                            {"cursor": "pointer"},
                        ),
                        disabled=rx.cond(
                            ChatState.messages.length() < 2,  # type: ignore
                            True,
                            False,
                        ),
                    ),
                ),
                rx.alert_dialog.content(
                    rx.alert_dialog.title("Check Conversation"),
                    rx.alert_dialog.description(
                        "Are you done with the exercise and want "
                        + "to check your conversation?"
                    ),
                    rx.hstack(
                        rx.alert_dialog.cancel(
                            rx.button(
                                "No",
                                color_scheme="red",
                                _hover={"cursor": "pointer"},
                            ),
                        ),
                        rx.alert_dialog.action(
                            rx.button(
                                "Yes",
                                color_scheme="iris",
                                on_click=ChatState.check_conversation,
                                _hover={"cursor": "pointer"},
                            ),
                        ),
                        margin_top="1em",
                    ),
                ),
            ),
        ),
    )


def submitted_status() -> rx.Component:
    """
    Render the status when the conversation is submitted.
    """
    return rx.hstack(
        rx.hover_card.root(
            rx.hover_card.trigger(
                rx.button(
                    rx.icon("eye", size=20),
                    color_scheme="iris",
                    on_click=rx.redirect(ChatState.finished_view_url),
                    _hover={"cursor": "pointer"},
                ),
            ),
            rx.hover_card.content(
                rx.text("View your submitted conversation"),
            ),
        ),
        rx.text(
            "Last submit: " + ChatState.submit_time_stamp,
            color_scheme="green",
        ),
        rx.icon(
            "circle-check",
            color="green",
            size=30,
        ),
        align="center",
    )


def not_submitted_status() -> rx.Component:
    """
    Render the status when the conversation is not submitted yet.
    """
    return rx.hstack(
        rx.icon(
            "info",
            color=rx.color_mode_cond(light="black", dark="white"),
            size=20,
        ),
        rx.text("Not submitted yet"),
        spacing="1",
        align="center",
    )


def show_exercise_status() -> rx.Component:
    """
    Show the status of the exercise, whether it is submitted or not.
    """
    return rx.cond(
        ChatState.conversation_is_submitted,
        submitted_status(),
        not_submitted_status(),
    )


@with_navbar
@require_role_at_least(UserRole.STUDENT)
def chat_page() -> rx.Component:
    """Renders the web page."""
    return rx.container(
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.hstack(
                        rx.button(
                            rx.icon("arrow-left", size=20),
                            color_scheme="iris",
                            on_click=rx.redirect(routes.EXERCISES),
                            _hover={"cursor": "pointer"},
                        ),
                        rx.heading(
                            "Exercise: " + ChatState.exercise_title,
                            size="5",
                        ),
                        align="center",
                    ),
                    show_exercise_status(),
                    align="center",
                    justify="between",
                    width="100%",
                ),
                rx.auto_scroll(
                    rx.foreach(
                        ChatState.messages,
                        message_box,
                    ),
                    scroll_to_bottom_on_update=True,
                    width="100%",
                    flex="1",
                    padding_right="8px",
                ),
                chat_form(),
                spacing="5",
                justify="start",
                min_height="85vh",
                max_height="85vh",
                height="100%",
            ),
            width="100%",
        ),
        align_items="center",
        width="100%",
    )
