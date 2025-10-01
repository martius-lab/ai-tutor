"""The pages for impressum and privacy notice."""

import pathlib
import reflex as rx
from aitutor.pages.navbar import with_navbar
from aitutor.language_state import LanguageState
from aitutor.config import get_config

_privacy_notice = None


def load_privacy_notice():
    """Load the privacy notice text from datenschutz.md."""
    global _privacy_notice
    try:
        with open(
            pathlib.Path(__file__).parent / "datenschutz.md", "r", encoding="utf-8"
        ) as f:
            _privacy_notice = f.read()
    except FileNotFoundError:
        print("Warning: datenschutz.md not found. Using empty privacy notice.")
        _privacy_notice = ""


def get_privacy_notice() -> str:
    """Get the privacy notice text from datenschutz.md."""
    if _privacy_notice is None:
        load_privacy_notice()
    assert _privacy_notice is not None
    return _privacy_notice


@with_navbar("")
def impressum_page() -> rx.Component:
    """Impressum page."""
    return rx.box(
        rx.vstack(
            rx.heading(LanguageState.impressum),
            rx.markdown(
                get_config().impressum_text,
                align="left",
            ),
            align="center",
        ),
        margin_top="2em",
        width="90%",
    )


@with_navbar("")
def privacy_notice_page() -> rx.Component:
    """Privacy Notice page."""
    return rx.box(
        rx.vstack(
            rx.heading(LanguageState.privacy_notice),
            rx.markdown(
                get_privacy_notice(),
                align="left",
            ),
            align="center",
        ),
        margin_top="2em",
        width="90%",
    )
