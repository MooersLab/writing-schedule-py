"""Data model for the writing-schedule Python port.

The types here mirror the plists produced by ``writing-schedule.el``:

- An :class:`Event` corresponds to a parsed time block.  Its five fields match
  the reference plist keys ``:section``, ``:offset``, ``:start``, ``:end``,
  and ``:letter`` (see the format spec, table ``tab:event``).
- A :class:`ParsedTable` corresponds to the plist returned by
  ``writing-schedule--parse`` with keys ``:events``, ``:legend``,
  ``:letters``, and ``:columns``.
- A :class:`MapEntry` corresponds to the mapping plists with keys
  ``:letter``, ``:code``, and ``:desc``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class Event:
    """One time block on one day.

    Attributes
    ----------
    section:
        The most recent section header, or ``"Writing"`` before any header.
    offset:
        Days from Monday (0 = Monday ... 6 = Sunday).
    start, end:
        Zero-padded ``HH:MM`` strings.
    letter:
        The upper-cased code taken from the day cell.
    """

    section: str
    offset: int
    start: str
    end: str
    letter: str


@dataclass
class ParsedTable:
    """The result of parsing a weekly block table."""

    events: List[Event] = field(default_factory=list)
    # Ordered list of (code, description) in first-appearance order.
    legend: List[Tuple[str, str]] = field(default_factory=list)
    # Sorted, de-duplicated list of codes (string< order).
    letters: List[str] = field(default_factory=list)
    # Ordered list of (column_index, day_offset).
    columns: List[Tuple[int, int]] = field(default_factory=list)

    def legend_lookup(self, code: str) -> Optional[str]:
        """Return the first description for ``code`` in the legend, or ``None``.

        This mirrors elisp ``assoc``, which returns the first matching entry.
        """
        for ltr, desc in self.legend:
            if ltr == code:
                return desc
        return None


@dataclass(frozen=True)
class MapEntry:
    """Assignment of a project to a code."""

    letter: str
    code: str = ""
    desc: str = ""


def map_get(mapping: List[MapEntry], letter: str) -> Optional[MapEntry]:
    """Return the mapping entry for ``letter``, or ``None``."""
    for m in mapping:
        if m.letter == letter:
            return m
    return None
