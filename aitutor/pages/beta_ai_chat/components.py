"""Components for the Beta AI chat skeleton page."""

import reflex as rx

from aitutor.pages.beta_ai_chat.state import BetaAIChatState


def beta_chat_header() -> rx.Component:
    """Render metadata for the selected Beta AI exercise."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading(BetaAIChatState.exercise_title, size="6"),
                rx.spacer(),
                rx.badge("Beta Chat Skeleton", color_scheme="purple"),
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
    """Render one skeleton chat message."""
    return rx.box(
        rx.vstack(
            rx.badge(
                rx.cond(message["role"] == "student", "Student", "Tutor"),
                color_scheme=rx.cond(message["role"] == "student", "blue", "green"),
            ),
            rx.text(message["content"], white_space="pre-wrap"),
            spacing="2",
            align="start",
        ),
        padding="1em",
        border_radius="8px",
        background_color=rx.cond(
            message["role"] == "student",
            rx.color("blue", 2),
            rx.color("green", 2),
        ),
        align_self=rx.cond(message["role"] == "student", "end", "start"),
        max_width="75%",
    )


def messages_panel() -> rx.Component:
    """Render the current in-memory chat messages."""
    return rx.card(
        rx.vstack(
            rx.heading("Conversation", size="4"),
            rx.cond(
                BetaAIChatState.messages.length() == 0,  # type: ignore
                rx.callout("No messages yet.", icon="info", width="100%"),
                rx.vstack(
                    rx.foreach(BetaAIChatState.messages, chat_message),
                    spacing="3",
                    width="100%",
                ),
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        width="100%",
    )


def message_input() -> rx.Component:
    """Render the skeleton student message input."""
    return rx.card(
        rx.vstack(
            rx.text_area(
                placeholder="Type a Beta AI chat message...",
                value=BetaAIChatState.student_message,
                on_change=BetaAIChatState.set_student_message,
                rows="4",
                width="100%",
            ),
            rx.hstack(
                rx.spacer(),
                rx.button(
                    rx.icon("send"),
                    rx.cond(BetaAIChatState.running_diagnosis, "Diagnosing...", "Send"),
                    on_click=BetaAIChatState.send_message,
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
        width="100%",
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
        beta_chat_header(),
        messages_panel(),
        message_input(),
        diagnosis_status_card(),
        spacing="4",
        width="100%",
    )
