"""Reflex renderers for generated diagram UI actions."""

import reflex as rx

from aitutor.pages.chat.generated_ui import (
    DiagramEdge,
    DiagramNode,
    DiagramType,
    GeneratedUiAction,
)


def node_body(node: DiagramNode, marker: rx.Component) -> rx.Component:
    """Render shared diagram node content."""
    return rx.vstack(
        rx.hstack(
            marker,
            rx.text(node.label, weight="bold", size="3"),
            spacing="2",
            align="center",
        ),
        rx.cond(
            node.detail != "",
            rx.text(node.detail, size="2", color=rx.color("gray", 11)),
        ),
        spacing="2",
        align="start",
        background_color="white",
        border=f"1px solid {rx.color('gray', 5)}",
        border_radius="8px",
        box_shadow="0 10px 30px rgba(15, 23, 42, 0.07)",
        padding="0.9em",
        width="100%",
    )


def numbered_marker(node_index: int) -> rx.Component:
    """Render a sequence marker for flow diagrams."""
    return rx.badge(
        node_index + 1,
        variant="solid",
        radius="full",
        min_width="1.75rem",
        height="1.75rem",
        justify_content="center",
    )


def concept_marker() -> rx.Component:
    """Render a non-sequential marker for concept maps."""
    return rx.box(
        rx.icon("sparkle", size=14),
        background_color=rx.color("accent", 9),
        color="white",
        border_radius="999px",
        width="1.75rem",
        height="1.75rem",
        display="flex",
        align_items="center",
        justify_content="center",
        flex_shrink="0",
    )


def root_marker() -> rx.Component:
    """Render the central concept marker."""
    return rx.box(
        rx.icon("network", size=15),
        background_color=rx.color("accent", 9),
        color="white",
        border_radius="999px",
        width="1.9rem",
        height="1.9rem",
        display="flex",
        align_items="center",
        justify_content="center",
        flex_shrink="0",
    )


def edge_label(edge: DiagramEdge, icon: str = "arrow-right") -> rx.Component:
    """Render an edge label directly on a connector."""
    return rx.badge(
        rx.hstack(
            rx.icon(icon, size=13),
            rx.text(rx.cond(edge.label != "", edge.label, "related"), size="1"),
            spacing="1",
            align="center",
        ),
        variant="surface",
        color_scheme="gray",
        radius="full",
    )


def flow_connector(edge: DiagramEdge) -> rx.Component:
    """Render a flow edge between two ordered steps."""
    return rx.hstack(
        rx.box(height="1px", background_color=rx.color("accent", 7), flex="1"),
        edge_label(edge, "arrow-down"),
        rx.box(height="1px", background_color=rx.color("accent", 7), flex="1"),
        width="100%",
        align="center",
        spacing="2",
        padding_x="0.5em",
    )


def flow_step(
    action: GeneratedUiAction,
    node: DiagramNode,
    node_index: int,
) -> rx.Component:
    """Render one ordered flow step and its following edge."""
    is_last_node = node_index == action.nodes.length() - 1  # type: ignore
    return rx.vstack(
        node_body(node, numbered_marker(node_index)),
        rx.cond(
            is_last_node,
            rx.fragment(),
            flow_connector(action.edges[node_index]),
        ),
        spacing="2",
        width="100%",
    )


def flow_surface(action: GeneratedUiAction) -> rx.Component:
    """Render a diagram as an ordered vertical flow."""
    return rx.box(
        rx.vstack(
            rx.foreach(
                action.nodes,
                lambda node, node_index: flow_step(action, node, node_index),
            ),
            spacing="2",
            width="100%",
        ),
        background_color=rx.color("gray", 1),
        border=f"1px solid {rx.color('gray', 5)}",
        border_radius="8px",
        padding="1em",
        width="100%",
    )


def branch_connector(edge: DiagramEdge) -> rx.Component:
    """Render a branch connector with the edge label attached to it."""
    return rx.vstack(
        rx.box(
            height="1.15rem",
            width="2px",
            background_color=rx.color("accent", 7),
        ),
        edge_label(edge, "corner-down-right"),
        spacing="1",
        align="center",
        width="100%",
    )


def branch_card(
    action: GeneratedUiAction,
    node: DiagramNode,
    node_index: int,
) -> rx.Component:
    """Render one branch in a concept-map diagram."""
    return rx.cond(
        node_index == 0,
        rx.fragment(),
        rx.vstack(
            branch_connector(action.edges[node_index - 1]),
            node_body(node, concept_marker()),
            spacing="2",
            width="100%",
            min_width="0",
        ),
    )


def concept_surface(action: GeneratedUiAction) -> rx.Component:
    """Render generated nodes as a hub-and-branch concept map."""
    return rx.box(
        rx.vstack(
            rx.box(
                node_body(action.nodes[0], root_marker()),
                width=["100%", "100%", "58%"],
                margin_x="auto",
            ),
            rx.box(
                height="1px",
                width=["72%", "78%", "84%"],
                background_color=rx.color("accent", 7),
                margin_x="auto",
                margin_top="1.2em",
            ),
            rx.grid(
                rx.foreach(
                    action.nodes,
                    lambda node, node_index: branch_card(action, node, node_index),
                ),
                columns=rx.breakpoints(initial="1", sm="2", md="3"),
                spacing="3",
                width="100%",
            ),
            spacing="0",
            align="stretch",
        ),
        background_color=rx.color("gray", 1),
        border=f"1px solid {rx.color('gray', 5)}",
        border_radius="8px",
        padding="1em",
        width="100%",
    )


def caption(action: GeneratedUiAction) -> rx.Component:
    """Render optional generated diagram caption text."""
    return rx.cond(
        action.caption != "",
        rx.text(action.caption, size="2", color=rx.color("gray", 11)),
    )


def diagram_header(action: GeneratedUiAction) -> rx.Component:
    """Render a generated diagram header."""
    return rx.hstack(
        rx.icon(
            rx.cond(action.diagram_type == DiagramType.FLOW, "route", "network"),
            size=18,
        ),
        rx.text(action.title, weight="bold", size="4"),
        rx.badge(action.diagram_type, variant="soft"),
        align="center",
        spacing="2",
    )


def diagram_surface(action: GeneratedUiAction) -> rx.Component:
    """Render the diagram with a layout matching its declared type."""
    return rx.cond(
        action.diagram_type == DiagramType.FLOW,
        flow_surface(action),
        concept_surface(action),
    )


def show_diagram_action(action: GeneratedUiAction) -> rx.Component:
    """Render a generated typed diagram."""
    return rx.box(
        rx.vstack(
            diagram_header(action),
            diagram_surface(action),
            caption(action),
            spacing="3",
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
