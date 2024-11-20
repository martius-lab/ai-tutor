"""Docstring."""

import reflex as rx


def chat_window_default(*args, **kwargs) -> rx.Component:  # noqa: D103
    return rx.container(
        # Äußere Box zur Zentrierung der gesamten Chat-UI
        rx.box(
            padding="20px",  # Padding um den gesamten Inhalt
            display="flex",
            flex_direction="column",
            align_items="center",
            justify_content="center",
            gap="20px",  # Abstand zwischen den Elementen
            width="100%",  # Breite des Containers
            max_width="600px",
            height="25vh",  # Volle Bildschirmhöhe für vertikale Zentrierung
        ),
        # Chatverlauf Container mit rx.scroll_area
        rx.scroll_area(
            rx.box(
                # Beispielnachrichten
                rx.text(
                    "Hallo! Wie kann ich dir helfen?",
                    color="green",
                    align="left",
                    padding="10px",
                    margin="5px",
                    background="lightgreen",
                    border_radius="5px",
                ),
                rx.text(
                    "Ich möchte Deutsch lernen!",
                    color="blue",
                    align="right",
                    padding="10px",
                    margin="5px",
                    background="lightgray",
                    border_radius="5px",
                ),
            ),
            max_height="400px",
            overflow_y="scroll",
            padding="10px",  # Padding innerhalb des scroll_area für bessere Lesbarkeit
        ),
        # Eingabefeld und Senden-Button mit Abstand
        rx.box(
            rx.input(placeholder="Schreibe hier deine Nachricht...", flex="1"),
            rx.button("Senden", margin_left="10px"),
            display="flex",
            padding="10px",
            align_items="center",
        ),
    )
