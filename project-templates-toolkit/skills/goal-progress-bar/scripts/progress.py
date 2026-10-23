#!/usr/bin/env python3
"""Render a weighted goal tracker.

Usage:
    python3 scripts/progress.py <tracker.json> ["<title>"] [--chat]

The tracker is a JSON list of [name, weight, fraction] rows. Fractions range
from 0.0 to 1.0. An optional fourth field, "blocked", marks a row that cannot
move. The title defaults to the tracker file name.
"""

import json
import sys
from decimal import Decimal
from pathlib import Path

USAGE = 'usage: progress.py <tracker.json> ["<title>"] [--chat]'


def row_percent(fraction):
    # Floor like the overall value, so an unfinished row never shows 100%.
    value = int(fraction * 100)
    return "<1%" if value == 0 else f"{value}%"


def status(row):
    """Return the display status for one validated tracker row."""
    fraction = row[2]
    if fraction >= 1:
        return "done"
    if len(row) > 3:
        return "blocked"
    return "in progress" if fraction > 0 else "not started"


def main(argv):
    """Validate arguments and print the current tracker."""
    chat = "--chat" in argv
    args = [arg for arg in argv if arg != "--chat"]
    if len(args) not in (1, 2) or argv.count("--chat") > 1:
        print(USAGE, file=sys.stderr)
        return 2

    path = Path(args[0])
    title = args[1] if len(args) == 2 else path.stem
    items = json.loads(path.read_text(encoding="utf-8"), parse_float=Decimal)

    for row in items:
        if not isinstance(row, list) or len(row) not in (3, 4):
            raise SystemExit(f"bad row: {row!r}")
        name, weight, fraction = row[:3]
        flag = row[3] if len(row) == 4 else None
        if not (
            isinstance(name, str)
            and isinstance(weight, (int, Decimal))
            and not isinstance(weight, bool)
            and weight > 0
            and isinstance(fraction, (int, Decimal))
            and not isinstance(fraction, bool)
            and 0 <= fraction <= 1
            and flag in (None, "blocked")
        ):
            raise SystemExit(f"bad row: {row!r}")

    total = sum(row[1] for row in items)
    done = sum(row[1] * row[2] for row in items)
    pct = 0 if total == 0 else (100 if done >= total else int(100 * done // total))

    if chat:
        width = 10
        fill = 0 if total == 0 else (width if pct == 100 else int(width * done // total))
        partial = 0 if total == 0 else int(fill < width and done * width > fill * total)
        bar = ":large_green_square:" * fill + ":large_yellow_square:" * partial
        bar += ":white_large_square:" * (width - fill - partial)
        print(f"*{title}*: {bar} {pct}%\n")
        circle = {
            "done": ":large_green_circle:",
            "in progress": ":large_yellow_circle:",
            "not started": ":white_circle:",
            "blocked": ":red_circle:",
        }
        for row in items:
            mark = status(row)
            extra = f" ({row_percent(row[2])})" if 0 < row[2] < 1 else ""
            print(f"{circle[mark]} {row[0]}{extra}")
    else:
        width = 30
        fill = 0 if total == 0 else int(width * done // total)
        print(f"{title}: [{'#' * fill}{'-' * (width - fill)}] {pct}%\n")
        for row in items:
            fraction = row[2]
            extra = f" ({row_percent(fraction)})" if 0 < fraction < 1 else ""
            print(f"- {row[0]}: {status(row)}{extra}")

    if not items:
        print("No progress rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
