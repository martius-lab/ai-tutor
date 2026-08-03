"""Printing colored and styled text to the terminal using ANSI codes.

The ``cprint`` function allows to easily print text with color and style (bold/faint).
It is relatively basic but good enough for our purposes, so we don't need to add a
third-party dependency for this.

Example:
```python
cprint("Hello, World!", fg="green")
cprint("Error!", fg="white", bg="red", style="bold")
```
"""

from typing import Literal, cast

color_codes_fg = {
    "black": "30",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "white": "37",
}

color_codes_bg = {
    "black": "40",
    "red": "41",
    "green": "42",
    "yellow": "43",
    "blue": "44",
    "magenta": "45",
    "cyan": "46",
    "white": "47",
}

style_codes = {
    "bold": "1",
    "faint": "2",
}

_color_t = Literal[
    "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"
]
_style_t = Literal["bold", "faint"]


def cprint(
    text: str,
    *,
    fg: _color_t | None = None,
    bg: _color_t | None = None,
    style: _style_t | None = None,
) -> None:
    """
    Print styled/colored text to the terminal using ANSI codes.

    Args:
        text: The text to print.
        fg: The foreground color. One of "black", "red", "green", "yellow", "blue",
            "magenta", "cyan", or "white".
        bg: The background color. One of "black", "red", "green", "yellow", "blue",
            "magenta", "cyan", or "white".
        style: The text style. One of "bold" or "faint".
    """
    codes = []
    if fg is not None:
        codes.append(color_codes_fg[fg])
    if bg is not None:
        codes.append(color_codes_bg[bg])
    if style is not None:
        codes.append(style_codes[style])
    code_seq = ";".join(codes)

    print(f"\x1b[{code_seq}m{text}\x1b[0m")


def showcase() -> None:
    """Showcase the available colors and styles."""
    for style in [None, "bold", "faint"]:
        for fg in color_codes_fg.keys():
            for bg in color_codes_bg.keys():
                cprint(
                    f"fg={fg}, bg={bg}, style={style}",
                    fg=cast(_color_t, fg),
                    bg=cast(_color_t, bg),
                    style=style,
                )
