"""The pages for impressum and privacy notice."""

import reflex as rx

from aitutor import DisplayConfigState
from aitutor.language_state import LanguageState
from aitutor.pages.legal_infos.loader_functions import get_privacy_notice
from aitutor.pages.navbar import with_navbar


@with_navbar("")
def impressum_page() -> rx.Component:
    """Impressum page."""
    return rx.box(
        rx.vstack(
            rx.heading(LanguageState.impressum),
            rx.markdown(
                DisplayConfigState.impressum_text,
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
