"""all global variables"""

import reflex as rx

TIME_FORMAT = "%d.%m.%Y %H:%M:%S MEZ"
TIME_ZONE = "Europe/Berlin"
SEARCH_USER_KEY = "user"
SEARCH_EXERCISE_KEY = "exercise"
SEARCH_TAG_KEY = "tag"

# ---- Chat related global variables ----
CHAT_TOKEN_WARNING_THRESHOLD = 0.8  # Show warning at x% of limit
CHAT_MESSAGE_CHAR_LIMIT = 15000

"""colors"""
GREEN_CHECK_COLOR = rx.color("green", 9)
