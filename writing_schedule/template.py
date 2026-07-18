"""Blank weekly-table scaffold.

Ports ``writing-schedule--template-string``.  The scaffold uses single-letter
codes; a user may rename the legend rows and use their own short uppercase
codes (such as EM or EX) in the cells.
"""

from __future__ import annotations

from typing import List

from .config import DEFAULT_SLOTS, PROJECT_LETTERS


def _blank_row(label: str, nd: int) -> str:
    return "| " + label + " |" + "  |" * nd + "\n"


def template_string(n: int) -> str:
    """Return a blank weekly schedule template for ``n`` projects (1..26)."""
    n = max(1, min(len(PROJECT_LETTERS), int(n)))
    days = ["M", "Tu", "W", "Th", "F", "Sa"]
    nd = len(days)
    letters = PROJECT_LETTERS[:n]

    parts: List[str] = []
    plural = "" if n == 1 else "s"
    parts.append(f"#+TITLE: Writing Schedule for {n} Project{plural}\n\n")
    parts.append("| Time <l> | " + " | ".join(days) + " |\n")
    parts.append("|-\n")
    for name, slots in DEFAULT_SLOTS:
        parts.append(_blank_row(name + ":", nd))
        for slot in slots:
            parts.append(_blank_row(slot, nd))
        parts.append("|-\n")
    for ltr in letters:
        parts.append(_blank_row(ltr + ":", nd))
    parts.append("|-\n")
    return "".join(parts)
