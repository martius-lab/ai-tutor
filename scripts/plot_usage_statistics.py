#!/usr/bin/env python3
"""Render the output of ``usage_statistics.py`` as a one-page report.

The page shows the overall totals as text and a bar chart comparing the lectures
(members by role, exercises, submissions and used tokens).  The output format is
derived from the file extension of ``--output`` (e.g. pdf, png or svg).

    uv run ./scripts/plot_usage_statistics.py stats.json -o usage_report.pdf
    uv run ./scripts/usage_statistics.py | uv run ./scripts/plot_usage_statistics.py
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure, FigureBase

SURFACE = "#ffffff"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#d8d7d2"
NEUTRAL_BAR = "#00373a"
# Member roles in stacking order, with their label and color.
ROLES = [
    ("STUDENT", "Students", "#00373a"),
    ("TUTOR", "Tutors", "#1b4e51"),
    ("OWNER", "Owners", "#356669"),
]

# Sizes in inches.  The width is that of an A4 page in portrait orientation.
PAGE_WIDTH = 8.27
PAGE_MARGIN = 0.6
HEADER_HEIGHT = 1.4
LECTURE_HEIGHT = 0.3
CHART_PADDING = 1.2


def parse_args() -> argparse.Namespace:
    """Parse the command line arguments."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help="JSON file from usage_statistics.py.  Reads stdin if omitted or '-'.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("usage_report.pdf"),
        help="Output file (default: %(default)s).",
    )
    return parser.parse_args()


def load_statistics(path: str) -> dict[str, Any]:
    """Load the statistics from the given file or stdin if ``path`` is '-'."""
    if path == "-":
        return json.load(sys.stdin)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def compact(value: int) -> str:
    """Format a number in a compact way, e.g. 1234 as "1.2K"."""
    for divisor, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if (scaled := round(value / divisor, 1)) >= 1:
            return f"{scaled:g}{suffix}"
    return str(value)


def format_total(value: int) -> str:
    """Format a total for the header, using the compact form for large values."""
    return compact(value) if value >= 10_000_000 else f"{value:,}"


def from_top(inches: float) -> float:
    """Convert a distance from the top of the header to a figure coordinate."""
    return 1 - inches / HEADER_HEIGHT


def draw_header(fig: FigureBase, statistics: dict[str, Any]) -> None:
    """Draw the title and the overall totals."""
    lectures = statistics["lectures"]["items"]
    generated_at = datetime.fromisoformat(statistics["generated_at"])
    tiles = [
        ("Users", statistics["users"]["total"]),
        ("Lectures", statistics["lectures"]["total"]),
        ("Submissions", sum(lec["submissions"] for lec in lectures)),
        ("Tokens used", statistics["tokens_used_total"]),
    ]

    fig.text(
        0,
        from_top(0),
        "AI Tutor – Usage Statistics",
        fontsize=18,
        fontweight="bold",
        color=TEXT_PRIMARY,
        va="top",
    )
    fig.text(
        1,
        from_top(0),
        f"Generated {generated_at:%Y-%m-%d %H:%M}",
        fontsize=9,
        color=TEXT_SECONDARY,
        ha="right",
        va="top",
    )
    for i, (label, value) in enumerate(tiles):
        x = i / len(tiles)
        fig.text(x, from_top(0.7), label, fontsize=10, color=TEXT_SECONDARY)
        fig.text(
            x,
            from_top(0.8),
            format_total(value),
            fontsize=20,
            fontweight="bold",
            color=TEXT_PRIMARY,
            va="top",
        )


def style_panel(ax: Axes, title: str, max_value: float) -> None:
    """Apply the common style of a chart panel."""
    ax.set_title(title, loc="left", fontsize=11, color=TEXT_PRIMARY, pad=10)
    # Leave room for the value labels at the end of the bars.
    ax.set_xlim(0, max(max_value, 1) * 1.3)
    ax.xaxis.set_visible(False)
    ax.tick_params(axis="y", length=0, labelsize=9, labelcolor=TEXT_PRIMARY)
    for side in ("top", "right", "bottom"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(GRID)


def label_bars(ax: Axes, values: list[int]) -> None:
    """Write the values next to the end of the bars."""
    for y, value in enumerate(values):
        ax.annotate(
            compact(value),
            (value, y),
            xytext=(4, 0),
            textcoords="offset points",
            va="center",
            fontsize=9,
            color=TEXT_SECONDARY,
        )


def draw_lectures(fig: FigureBase, lectures: list[dict[str, Any]]) -> None:
    """Draw the bar chart comparing the lectures."""
    fig.suptitle(
        "Lectures",
        x=0,
        ha="left",
        fontsize=14,
        fontweight="bold",
        color=TEXT_PRIMARY,
    )
    if not lectures:
        fig.text(0.5, 0.5, "No lectures.", ha="center", color=TEXT_SECONDARY)
        return

    lectures = sorted(lectures, key=lambda lec: lec["members"]["total"])
    names = [textwrap.fill(lec["name"], 34) for lec in lectures]
    positions = list(range(len(lectures)))
    bar_options = {"height": 0.55, "linewidth": 0}

    axes = fig.subplots(1, 4, sharey=True)
    members_ax = axes[0]
    left = [0] * len(lectures)
    for role, label, color in ROLES:
        counts = [lec["members"].get(role, 0) for lec in lectures]
        members_ax.barh(
            positions, counts, left=left, color=color, label=label, **bar_options
        )
        left = [a + b for a, b in zip(left, counts, strict=True)]
    totals = [lec["members"]["total"] for lec in lectures]
    label_bars(members_ax, totals)
    style_panel(members_ax, "Members", max(totals))
    fig.legend(
        loc="outside lower left",
        ncol=len(ROLES),
        frameon=False,
        fontsize=9,
        handlelength=1,
        columnspacing=1,
        labelcolor=TEXT_SECONDARY,
    )

    for ax, key, title in [
        (axes[1], "exercises", "Exercises"),
        (axes[2], "submissions", "Submissions"),
        (axes[3], "tokens_used", "Tokens used"),
    ]:
        values = [lec[key] for lec in lectures]
        ax.barh(positions, values, color=NEUTRAL_BAR, **bar_options)
        label_bars(ax, values)
        style_panel(ax, title, max(values))

    members_ax.set_yticks(positions, names)

    # Left-align the lecture names by shifting them left by the width of the longest
    # one.  The width is only known after drawing.
    from matplotlib.figure import Figure

    root = fig.figure
    assert isinstance(root, Figure)
    root.draw_without_rendering()
    labels = members_ax.get_yticklabels()
    max_width = max(label.get_window_extent().width for label in labels)
    members_ax.tick_params(axis="y", pad=max_width * 72 / root.dpi + 8)
    for label in labels:
        label.set_horizontalalignment("left")
        label.set_linespacing(1.0)


def build_report(statistics: dict[str, Any]) -> Figure:
    """Build the report page."""
    from matplotlib.figure import Figure
    from matplotlib.layout_engine import ConstrainedLayoutEngine

    lectures = statistics["lectures"]["items"]
    chart_height = CHART_PADDING + LECTURE_HEIGHT * max(len(lectures), 1)
    height = HEADER_HEIGHT + chart_height + 2 * PAGE_MARGIN
    margin_x = PAGE_MARGIN / PAGE_WIDTH
    margin_y = PAGE_MARGIN / height
    fig = Figure(
        figsize=(PAGE_WIDTH, height),
        facecolor=SURFACE,
        layout=ConstrainedLayoutEngine(
            rect=(margin_x, margin_y, 1 - 2 * margin_x, 1 - 2 * margin_y)
        ),
    )
    header, chart = fig.subfigures(  # type: ignore
        2, 1, height_ratios=[HEADER_HEIGHT, chart_height], facecolor=SURFACE
    )
    draw_header(header, statistics)
    draw_lectures(chart, lectures)
    return fig


def main() -> int:
    """Run the script."""
    args = parse_args()
    statistics = load_statistics(args.input)
    build_report(statistics).savefig(args.output, dpi=200)
    print(f"Report written to {args.output}.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
