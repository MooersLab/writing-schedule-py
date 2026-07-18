"""Parse a weekly block table into a :class:`ParsedTable`.

This is a direct port of ``writing-schedule--parse`` plus its helpers.  The
four row kinds (header, legend, time-block, section header) are tested in that
order and the first match wins, exactly as in the reference.  See the format
spec sections "The weekly block table".
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

from .model import Event, ParsedTable
from .orgtable import HLINE, Row, parse_org_table

# Map a lower-cased day abbreviation to an offset from Monday.
# Mirrors ``writing-schedule--day-alist`` exactly.
_DAY_ALIST = {
    "m": 0, "mo": 0, "mon": 0,
    "tu": 1, "tue": 1,
    "w": 2, "we": 2, "wed": 2,
    "th": 3, "thu": 3,
    "f": 4, "fr": 4, "fri": 4,
    "sa": 5, "sat": 5,
    "su": 6, "sun": 6,
}

# A start time and an end time inside a label cell.  Whitespace after a colon
# is tolerated, so "16: 30" reads as 16:30.  Mirrors
# ``writing-schedule--time-regexp``.
_TIME_RE = re.compile(
    r"([0-9]{1,2}):[ \t]*([0-9]{2})[ \t]*-+[ \t]*([0-9]{1,2}):[ \t]*([0-9]{2})"
)

# Case-sensitive.  A short uppercase code, then a colon.
_LEGEND_RE = re.compile(r"^([A-Z][A-Z0-9]{0,3})[ \t]*:(.*)$")

# A section header: letters and spaces only, optional trailing colon.
_SECTION_RE = re.compile(r"^[A-Za-z][A-Za-z ]*:?$")


def day_offset(cell: Optional[str]) -> Optional[int]:
    """Return the Monday offset for ``cell`` when it names a day, else None."""
    return _DAY_ALIST.get((cell or "").strip().lower())


def parse_time(cell: Optional[str]) -> Optional[Tuple[str, str]]:
    """Return (start, end) as zero-padded ``HH:MM`` strings, or None.

    The range may appear anywhere inside the cell.  No range checking is done,
    matching the reference; callers may validate separately.
    """
    if not cell:
        return None
    m = _TIME_RE.search(cell)
    if not m:
        return None
    sh, sm, eh, em = (int(m.group(i)) for i in range(1, 5))
    return (f"{sh:02d}:{sm:02d}", f"{eh:02d}:{em:02d}")


def minutes_between(start: str, end: str) -> int:
    """Return the number of minutes between two ``HH:MM`` strings."""
    s = 60 * int(start[0:2]) + int(start[3:5])
    e = 60 * int(end[0:2]) + int(end[3:5])
    return e - s


def parse_table(rows: List[Row]) -> ParsedTable:
    """Parse table ``rows`` (from :func:`parse_org_table`) into a ParsedTable."""
    columns: List[Tuple[int, int]] = []   # (col_index, day_offset)
    section: Optional[str] = None
    events: List[Event] = []
    legend: List[Tuple[str, str]] = []
    letters: List[str] = []

    for row in rows:
        if row == HLINE:
            continue
        cells = [(c or "").strip() for c in row]
        if not cells:
            continue
        label = cells[0]

        # Row kind one: the header row (only until columns are found).
        if not columns and any(day_offset(c) is not None for c in cells[1:]):
            for i, c in enumerate(cells):
                off = day_offset(c)
                if off is not None and i > 0:
                    columns.append((i, off))
            continue

        # Row kind two: the legend row (case-sensitive).
        m = _LEGEND_RE.match(label)
        if m:
            ltr = m.group(1).upper()
            desc = m.group(2).strip()
            if desc == "":
                desc = " ".join(cells[1:]).strip()
            legend.append((ltr, desc))
            continue

        # Row kind three: the time-block row (requires day columns).
        rng = parse_time(label) if columns else None
        if columns and rng is not None:
            for col_index, off in columns:
                cell = cells[col_index] if col_index < len(cells) else ""
                if cell:
                    ltr = cell.upper()
                    events.append(
                        Event(
                            section=section or "Writing",
                            offset=off,
                            start=rng[0],
                            end=rng[1],
                            letter=ltr,
                        )
                    )
                    if ltr not in letters:
                        letters.append(ltr)
            continue

        # Row kind four: the section header.
        if label and _SECTION_RE.match(label) and parse_time(label) is None:
            section = label.replace(":", "").strip()
            continue
        # Otherwise ignore the row.

    return ParsedTable(
        events=events,
        legend=legend,
        letters=sorted(letters),
        columns=columns,
    )


def parse_text(text: str) -> ParsedTable:
    """Convenience: read the first org table in ``text`` and parse it."""
    return parse_table(parse_org_table(text))
