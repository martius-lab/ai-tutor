"""Functions to load legal info texts."""

import pathlib


def get_privacy_notice() -> str:
    """Get the privacy notice text from datenschutz.md."""
    try:
        with open(
            pathlib.Path(__file__).parent / "datenschutz.md", "r", encoding="utf-8"
        ) as f:
            return f.read()
    except FileNotFoundError:
        print("Warning: datenschutz.md not found. Using empty privacy notice.")
        return ""


def get_privacy_notice_short() -> str:
    """Get the short privacy notice text from datenschutz_short.md."""
    try:
        with open(
            pathlib.Path(__file__).parent / "datenschutz_short.md",
            "r",
            encoding="utf-8",
        ) as f:
            return f.read()
    except FileNotFoundError:
        print(
            "Warning: datenschutz_short.md not found. Using empty short privacy notice."
        )
        return ""
