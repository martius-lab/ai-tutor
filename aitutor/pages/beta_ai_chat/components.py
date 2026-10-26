"""Components for the Beta AI chat skeleton page."""

import reflex as rx

import aitutor.global_vars as gv
from aitutor.pages.beta_ai_chat.state import BetaAIChatState


def beta_chat_header() -> rx.Component:
    """Render metadata for the selected Beta AI exercise."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading(BetaAIChatState.exercise_title, size="6"),
                rx.spacer(),
                rx.badge("Beta Chat", color_scheme="purple"),
                width="100%",
                align="center",
            ),
            rx.cond(
                BetaAIChatState.exercise_description,
                rx.text(BetaAIChatState.exercise_description, color_scheme="gray"),
            ),
            rx.cond(
                BetaAIChatState.source_material_filename,
                rx.callout(
                    "Source file: " + BetaAIChatState.source_material_filename,
                    icon="file-text",
                    width="100%",
                ),
            ),
            rx.callout(
                BetaAIChatState.concept_summary,
                icon="target",
                width="100%",
            ),
            rx.hstack(
                rx.badge(BetaAIChatState.concept_progress_label, color_scheme="purple"),
                rx.button(
                    rx.icon("chevron-left"),
                    "Previous concept",
                    size="2",
                    variant="soft",
                    on_click=BetaAIChatState.go_to_previous_concept,
                    disabled=~BetaAIChatState.can_go_previous_concept,
                    _hover=rx.cond(
                        BetaAIChatState.can_go_previous_concept,
                        {"cursor": "pointer"},
                        {"cursor": "not-allowed"},
                    ),
                ),
                rx.button(
                    "Next concept",
                    rx.icon("chevron-right"),
                    size="2",
                    variant="soft",
                    on_click=BetaAIChatState.go_to_next_concept,
                    disabled=~BetaAIChatState.can_go_next_concept,
                    _hover=rx.cond(
                        BetaAIChatState.can_go_next_concept,
                        {"cursor": "pointer"},
                        {"cursor": "not-allowed"},
                    ),
                ),
                spacing="2",
                wrap="wrap",
                align="center",
            ),
            rx.callout(
                BetaAIChatState.concept_state_summary,
                icon="chart-no-axes-column-increasing",
                width="100%",
            ),
            rx.callout(
                BetaAIChatState.level_status_summary,
                icon="layers-3",
                width="100%",
            ),
            rx.callout(
                BetaAIChatState.cumulative_evidence_summary,
                icon="list-checks",
                width="100%",
                white_space="pre-wrap",
            ),
            rx.callout(
                "This chat diagnoses each message as a latest turn, then "
                "uses cumulative concept evidence for policy decisions.",
                icon="info",
                width="100%",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        width="100%",
    )


def chat_message(message: dict[str, str]) -> rx.Component:
    """Render one Beta AI chat message using the normal exercise chat bubble style."""
    return rx.box(
        rx.markdown(
            message["content"].replace("\n", "  \n"),
            background_color=rx.cond(
                message["role"] == "student",
                rx.color("accent", 3),
                rx.color("gray", 3),
            ),
            color=rx.cond(
                message["role"] == "student",
                rx.color("accent", 12),
                rx.color("gray", 12),
            ),
            text_align="left",
            display="inline-block",
            padding="1em",
            border_radius="8px",
            max_width=["30em", "30em", "50em", "50em", "50em", "50em"],
        ),
        text_align=rx.cond(
            message["role"] == "student",
            "right",
            "left",
        ),
        margin_top="1em",
        width="100%",
    )


def messages_panel() -> rx.Component:
    """Render the current Beta AI chat messages in the normal chat scroll style."""
    return rx.box(
        rx.auto_scroll(
            rx.cond(
                BetaAIChatState.messages.length() == 0,  # type: ignore
                rx.callout("No messages yet.", icon="info", width="100%"),
                rx.foreach(BetaAIChatState.messages, chat_message),
            ),
            scroll_to_bottom_on_update=True,
            width="100%",
            height="100%",
            padding_right="8px",
        ),
        width="100%",
        height="45vh",
        min_height="16em",
        overflow_y="auto",
    )


def message_input() -> rx.Component:
    """Render the Beta AI student message input in the normal chat form style."""

    def text_area_with_key_submit(with_key_submit: bool) -> rx.Component:
        return rx.text_area(
            name="student_message",
            placeholder="Your answer",
            value=BetaAIChatState.student_message,
            on_change=BetaAIChatState.set_student_message,
            required=True,
            width="100%",
            max_height="40vh",
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
                beta_submit_button(),
                rx.spacer(),
                rx.button(
                    rx.icon("send-horizontal", size=20),
                    type="submit",
                    loading=BetaAIChatState.running_diagnosis,
                    disabled=~BetaAIChatState.can_send_message,
                    _hover=rx.cond(
                        BetaAIChatState.can_send_message,
                        {"cursor": "pointer"},
                        {"cursor": "not-allowed"},
                    ),
                ),
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        on_submit=BetaAIChatState.send_message,
        reset_on_submit=True,
    )


def beta_submit_button() -> rx.Component:
    """Render the Beta AI submit button in the chat action row."""
    return rx.button(
        "Submit",
        color_scheme="green",
        type="button",
        on_click=BetaAIChatState.submit_beta_conversation,
        disabled=rx.cond(
            BetaAIChatState.completion_unlocked,
            False,
            True,
        ),
        _hover=rx.cond(
            BetaAIChatState.completion_unlocked,
            {"cursor": "pointer"},
            {"cursor": "not-allowed"},
        ),
    )


def beta_submission_status() -> rx.Component:
    """Render compact Beta AI submission status for the page header."""
    return rx.cond(
        BetaAIChatState.conversation_is_submitted,
        rx.hstack(
            rx.hover_card.root(
                rx.hover_card.trigger(
                    rx.button(
                        rx.icon("eye", size=20),
                        on_click=rx.redirect(BetaAIChatState.beta_finished_view_url),
                        _hover={"cursor": "pointer"},
                    ),
                ),
                rx.hover_card.content(rx.text("View your Beta AI submission")),
            ),
            rx.desktop_only(
                rx.text(
                    "Last submit: " + BetaAIChatState.submit_time_stamp,
                    color_scheme="green",
                ),
            ),
            rx.icon("circle-check", color=gv.GREEN_CHECK_COLOR, size=30),
            align="center",
        ),
        rx.hstack(
            rx.icon("info", size=20),
            rx.text("Not submitted yet"),
            spacing="1",
            align="center",
        ),
    )


def diagnosis_status_card() -> rx.Component:
    """Render the latest diagnosis and policy status."""
    return rx.card(
        rx.vstack(
            rx.heading("Latest Diagnosis / Policy Preview", size="4"),
            rx.hstack(
                rx.badge(
                    BetaAIChatState.trace_history_count_label,
                    color_scheme="blue",
                ),
                rx.cond(
                    BetaAIChatState.has_trace_log_id,
                    rx.badge(
                        BetaAIChatState.last_trace_log_id_label,
                        color_scheme="gray",
                    ),
                ),
                spacing="2",
                wrap="wrap",
            ),
            rx.cond(
                BetaAIChatState.has_last_trace,
                rx.vstack(
                    rx.hstack(
                        rx.badge(BetaAIChatState.last_diagnosis_pattern),
                        rx.badge(
                            BetaAIChatState.last_policy_action, color_scheme="purple"
                        ),
                        rx.badge(
                            BetaAIChatState.last_policy_rule_id, color_scheme="gray"
                        ),
                        spacing="2",
                        wrap="wrap",
                    ),
                    rx.code_block(
                        BetaAIChatState.last_trace_json,
                        language="json",
                        width="100%",
                    ),
                    spacing="3",
                    align="start",
                    width="100%",
                ),
                rx.callout(
                    "No diagnosis has been run in this chat yet.",
                    icon="info",
                    width="100%",
                ),
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        width="100%",
    )


def beta_ai_chat_content() -> rx.Component:
    """Render the full Beta AI chat skeleton content."""
    return rx.vstack(
        messages_panel(),
        message_input(),
        spacing="4",
        width="100%",
    )
