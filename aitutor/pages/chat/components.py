"""The UI components for the chat page."""

import reflex as rx

from aitutor.pages.chat.state import ChatState, ChatMessage, Role


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
        rx.markdown(
            chat_message.message.replace("\n", "  \n"),  # transform to markdown newline
            background_color=rx.cond(
                chat_message.role == Role.CHECK_RESULT,
                rx.color(check_result_color, 4),
                rx.cond(
                    chat_message.role == Role.AITUTOR,
                    rx.color("mauve", 4),
                    rx.color("iris", 4),
                ),
            ),
            color=rx.cond(
                chat_message.role == Role.CHECK_RESULT,
                rx.color(check_result_color, 12),
                rx.cond(
                    chat_message.role == Role.AITUTOR,
                    rx.color("mauve", 12),
                    rx.color("iris", 12),
                ),
            ),
            text_align="left",
            display="inline-block",
            padding="1em",
            border_radius="8px",
            max_width=["30em", "30em", "50em", "50em", "50em", "50em"],
        ),
        text_align=rx.cond(
            chat_message.role == Role.USER,
            "right",
            "left",
        ),
        margin_top="1em",
        width="100%",
    )


def show_messages() -> rx.Component:
    """
    Displays the chat with all the messages
    """
    last_user_msg_i = ChatState.last_user_message_index
    return (
        rx.auto_scroll(
            rx.foreach(
                ChatState.messages,
                lambda msg, msg_i: rx.fragment(
                    rx.vstack(
                        message_box(msg),
                        rx.cond(
                            msg_i == last_user_msg_i,
                            rx.box(
                                edit_last_message_button(),
                                text_align="right",
                                width="100%",
                                margin_top="0.5em",
                            ),
                        ),
                        spacing="0",
                    ),
                ),
            ),
            scroll_to_bottom_on_update=True,
            width="100%",
            flex="1",
            padding_right="8px",
        ),
    )  # type: ignore


def chat_form() -> rx.Component:
    """
    Render the chat form for user input. Includes button to send Reply and button to
    check the conversation.
    """

    def text_area_with_key_submit(with_key_submit: bool) -> rx.Component:
        """
        Render a text area with enter key submit enabled or disabled.
        """
        return rx.text_area(
            name="user_response",
            placeholder="Your Answer",
            value=ChatState.user_input,
            on_change=ChatState.set_user_input,  # type: ignore (reflex has default setters)
            required=True,
            width="100%",
            max_height="40vh",
            color_scheme="iris",
            enter_key_submit=with_key_submit,
            resize="vertical",
            rows="4",
        )

    return rx.form(
        rx.vstack(
            rx.desktop_only(
                text_area_with_key_submit(True),
                width="100%",
            ),
            rx.mobile_and_tablet(
                text_area_with_key_submit(False),
                width="100%",
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


def edit_last_message_button() -> rx.Component:
    """
    Render the button to delete the last message.
    """
    return rx.alert_dialog.root(
        rx.alert_dialog.trigger(
            rx.button(
                rx.hstack(
                    rx.icon("trash", size=20),
                    rx.text("+", size="4"),
                    rx.icon("pencil", size=20),
                    spacing="1",
                    align="center",
                    justify="center",
                ),
                color_scheme="iris",
                _hover=rx.cond(
                    ChatState.waiting_for_response,
                    {"cursor": "not-allowed"},
                    {"cursor": "pointer"},
                ),
                disabled=rx.cond(
                    ChatState.waiting_for_response,
                    True,
                    False,
                ),
                type="button",
            ),
        ),
        rx.alert_dialog.content(
            rx.alert_dialog.title("Edit Last Message"),
            rx.alert_dialog.description(
                "Do you want to delete this message and move it to the input field?"
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
                        on_click=ChatState.edit_last_message,
                        _hover={"cursor": "pointer"},
                    ),
                ),
                margin_top="1em",
            ),
        ),
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
        disabled=ChatState.waiting_for_response,
    )


def reset_conversation_button() -> rx.Component:
    """
    Render the button to reset the conversation.
    """
    return (
        rx.alert_dialog.root(
            rx.alert_dialog.trigger(
                rx.button(
                    rx.desktop_only("Reset Conversation"),
                    rx.mobile_and_tablet("Reset"),
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
            ChatState.waiting_for_response,
            rx.button(
                rx.desktop_only("Check Conversation"),
                rx.mobile_and_tablet("Check"),
                color_scheme="yellow",
                type="button",
                _hover={"cursor": "not-allowed"},
                disabled=True,
            ),
            rx.alert_dialog.root(
                rx.alert_dialog.trigger(
                    rx.button(
                        rx.desktop_only("Check Conversation"),
                        rx.mobile_and_tablet("Check"),
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
