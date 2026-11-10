"""Badge that marks Level AI exercises in lists and headers."""

import reflex as rx

from aitutor.global_vars import LEVEL_AI_BADGE_COLOR_SCHEME
from aitutor.language_state import LanguageState


def level_ai_badge() -> rx.Component:
    """Render the shared badge for Level AI exercises."""
    return rx.badge(
        LanguageState.level_ai_badge_label, color_scheme=LEVEL_AI_BADGE_COLOR_SCHEME
    )
