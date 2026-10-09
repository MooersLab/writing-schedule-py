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

# A day cell with an activity letter before the code, as in gA, eB, or sEM.
# The letter counts only when it is lowercase and the code that follows starts
# with a capital, so a cell typed all in lowercase, such as "ga", is still the
# code GA.  Mirrors ``writing-schedule--cell-regexp``.
_CELL_RE = re.compile(r"^([ges])([A-Z][A-Z0-9]{0,3})$")

#: The section name each activity letter of a day cell stands for.  These are
#: the names the blank template uses, so a prefixed cell and a cell under the
#: matching header give the same event.
ACTIVITY_SECTION = {"g": "Generative", "e": "Rewriting", "s": "Supporting"}

# A default activity in a legend description, as in "E: email @support".
_LEGEND_ACTIVITY_RE = re.compile(
    r"(?:^|\s)@(generative|editing|support)\b", re.IGNORECASE)

#: The section name each legend default activity stands for.
LEGEND_ACTIVITY_SECTION = {
    "generative": "Generative", "editing": "Rewriting", "support": "Supporting"}


def split_cell(cell: Optional[str]) -> Tuple[Optional[str], str]:
    """Return ``(activity_letter or None, CODE)`` for a day cell.

    ``gA`` gives ``("g", "A")`` and ``A`` gives ``(None, "A")``.  A cell that
    does not carry a prefix is upper-cased whole, as before.
    """
    text = (cell or "").strip()
    m = _CELL_RE.match(text)
    if m:
        return m.group(1), m.group(2)
    return None, text.upper()


def split_legend_activity(desc: str) -> Tuple[str, Optional[str]]:
    """Return ``(description without the tag, activity or None)``.

    The tag is a word such as ``@support`` anywhere in the description, and
    the activity is returned in lowercase.  Only the first tag counts.
    """
    m = _LEGEND_ACTIVITY_RE.search(desc or "")
    if not m:
        return desc, None
    rest = (desc[:m.start()] + desc[m.end():]).strip()
    return re.sub(r"[ \t]{2,}", " ", rest), m.group(1).lower()


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
    # (header section or None, activity letter or None, offset, start, end, code)
    pending: List[Tuple[Optional[str], Optional[str], int, str, str, str]] = []
    legend: List[Tuple[str, str]] = []
    defaults: dict = {}                   # code -> section, first definition wins
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
            desc, activity = split_legend_activity(desc)
            if ltr not in {code for code, _d in legend}:
                defaults[ltr] = LEGEND_ACTIVITY_SECTION.get(activity or "")
            legend.append((ltr, desc))
            continue

        # Row kind three: the time-block row (requires day columns).
        rng = parse_time(label) if columns else None
        if columns and rng is not None:
            for col_index, off in columns:
                cell = cells[col_index] if col_index < len(cells) else ""
                if cell:
                    activity, ltr = split_cell(cell)
                    pending.append((section, activity, off, rng[0], rng[1], ltr))
                    if ltr not in letters:
                        letters.append(ltr)
            continue

        # Row kind four: the section header.
        if label and _SECTION_RE.match(label) and parse_time(label) is None:
            section = label.replace(":", "").strip()
            continue
        # Otherwise ignore the row.

    # The activity of a block comes from the first of these that is present:
    # a prefix in the cell, a default on the code's legend entry, the section
    # header above the row, and finally "Writing".  The legend usually sits
    # below the grid, so the defaults are applied once every row is read.
    events = [
        Event(section=(ACTIVITY_SECTION.get(activity or "") or defaults.get(ltr)
                       or header or "Writing"),
              offset=off, start=start, end=end, letter=ltr, activity=activity)
        for header, activity, off, start, end, ltr in pending
    ]
    return ParsedTable(
        events=events,
        legend=legend,
        letters=sorted(letters),
        columns=columns,
    )


def parse_text(text: str) -> ParsedTable:
    """Convenience: read the first org table in ``text`` and parse it."""
    return parse_table(parse_org_table(text))
