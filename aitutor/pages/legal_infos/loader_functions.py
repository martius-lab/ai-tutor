"""Functions to load legal info texts."""

import pathlib

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


_privacy_notice_short = None


def load_privacy_notice_short():
    """Load the short privacy notice text from datenschutz_short.md."""
    global _privacy_notice_short
    try:
        with open(
            pathlib.Path(__file__).parent / "datenschutz_short.md",
            "r",
            encoding="utf-8",
        ) as f:
            _privacy_notice_short = f.read()
    except FileNotFoundError:
        print(
            "Warning: datenschutz_short.md not found. Using empty short privacy notice."
        )
        _privacy_notice_short = ""


def get_privacy_notice_short() -> str:
    """Get the short privacy notice text from datenschutz_short.md."""
    if _privacy_notice_short is None:
        load_privacy_notice_short()
    assert _privacy_notice_short is not None
    return _privacy_notice_short
