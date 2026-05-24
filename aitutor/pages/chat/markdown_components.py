"""Markdown rendering helpers for chat messages."""

import reflex as rx


def _paragraph(value: object, **props) -> rx.Component:
    return rx.text(value, margin_y="0.4em", line_height="1.65", **props)


def _link(value: object, **props) -> rx.Component:
    return rx.link(
        value,
        color=rx.color("accent", 11),
        text_decoration="underline",
        text_underline_offset="0.15em",
        **props,
    )


def _table(value: object, **props) -> rx.Component:
    return rx.box(
        rx.table.root(value, variant="surface", size="1", width="100%", **props),
        overflow_x="auto",
        width="100%",
        margin_y="0.75em",
    )


def _thead(value: object, **props) -> rx.Component:
    return rx.table.header(value, **props)


def _tbody(value: object, **props) -> rx.Component:
    return rx.table.body(value, **props)


def _tr(value: object, **props) -> rx.Component:
    return rx.table.row(value, **props)


def _th(value: object, **props) -> rx.Component:
    return rx.table.column_header_cell(value, white_space="nowrap", **props)


def _td(value: object, **props) -> rx.Component:
    return rx.table.cell(value, vertical_align="top", **props)


def _inline_code(value: object, **props) -> rx.Component:
    return rx.code(value, variant="soft", **props)


CHAT_MARKDOWN_COMPONENTS = {
    "p": _paragraph,
    "a": _link,
    "table": _table,
    "thead": _thead,
    "tbody": _tbody,
    "tr": _tr,
    "th": _th,
    "td": _td,
    "code": _inline_code,
}


def chat_markdown(
    source: str,
    background_color,
    color,
) -> rx.Component:
    """Render GitHub-flavored Markdown inside a chat bubble."""
    return rx.markdown(
        source,
        component_map=CHAT_MARKDOWN_COMPONENTS,
        background_color=background_color,
        color=color,
        text_align="left",
        display="inline-block",
        padding="1em",
        border_radius="8px",
        max_width=["30em", "30em", "50em", "50em", "50em", "50em"],
        width="100%",
        overflow_x="auto",
    )
