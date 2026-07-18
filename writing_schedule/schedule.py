"""Generate the dated schedule ``.org`` file and its Summary section.

Ports ``writing-schedule--build-org`` and ``writing-schedule--summary`` plus
the batch mapping helper.  See the format spec, "The generated schedule file".
"""

from __future__ import annotations

import datetime as _dt
from typing import List, Optional, Tuple

from .config import Config
from .week import iso_date, timestamp, week_monday
from .model import Event, MapEntry, ParsedTable, map_get
from .parser import minutes_between


def legend_mapping(
    letters: List[str], legend: List[Tuple[str, str]]
) -> List[MapEntry]:
    """Build a non-interactive mapping for ``letters`` from ``legend``.

    Each entry has an empty code and a description taken from the legend, so
    batch generation needs no prompts.  Mirrors
    ``writing-schedule--legend-mapping``.
    """
    lookup = dict(legend)  # last wins here; the reference's assoc takes first.
    # Preserve first-appearance description to match elisp ``assoc``.
    first: dict = {}
    for code, desc in legend:
        first.setdefault(code, desc)
    return [MapEntry(letter=ltr, code="", desc=first.get(ltr, "")) for ltr in letters]


def _headline(entry: Optional[MapEntry], letter: str) -> str:
    """Choose headline text: description, then code, then ``Project X``."""
    if entry and entry.desc:
        return entry.desc
    if entry and entry.code:
        return entry.code
    return f"Project {letter}"


def build_org(
    events: List[Event],
    mapping: List[MapEntry],
    monday: _dt.date,
    title: str,
    config: Optional[Config] = None,
) -> str:
    """Return the schedule org file body (without the Summary section)."""
    cfg = config or Config()
    out: List[str] = []

    # Sections in first-appearance order among the events.
    sections: List[str] = []
    for ev in events:
        if ev.section not in sections:
            sections.append(ev.section)

    out.append(f"#+TITLE: {title}\n")
    out.append("#+FILETAGS: :writing:\n")
    out.append("#+LaTeX_HEADER: \\usepackage[margin=0.5in]{geometry}\n\n")
    out.append("# Letter to project map:\n")
    for m in mapping:
        tail = f" ({m.desc})" if m.desc else ""
        out.append(f"#   {m.letter} = {m.code}{tail}\n")
    out.append("\n")

    for s in sections:
        out.append(f"* {s}\n")
        out.append(f"  :PROPERTIES:\n  :CATEGORY: {s}\n  :END:\n")
        for ev in events:
            if ev.section != s:
                continue
            entry = map_get(mapping, ev.letter)
            code = entry.code if entry else ""
            head = _headline(entry, ev.letter)
            todo = f"{cfg.todo_keyword} " if cfg.use_todo else ""
            out.append(f"** {todo}{head} :{ev.letter}:\n")
            if code:
                out.append(f"   :PROPERTIES:\n   :WS_CODE: {code}\n   :END:\n")
            ts = timestamp(monday, ev.offset, ev.start, ev.end)
            out.append(f"   {ts}\n")

    return "".join(out)


def summary(events: List[Event], mapping: List[MapEntry]) -> str:
    """Return an org Summary section totalling weekly hours per code.

    The section carries no timestamp, so a calendar exporter skips it.
    """
    totals: dict = {}
    order: List[str] = []
    for ev in events:
        if ev.letter not in order:
            order.append(ev.letter)
        totals[ev.letter] = totals.get(ev.letter, 0) + minutes_between(
            ev.start, ev.end
        )
    order = sorted(order)

    lines = []
    for ltr in order:
        entry = map_get(mapping, ltr)
        label = _headline(entry, ltr)
        hours = totals.get(ltr, 0) / 60.0
        lines.append(f"- {ltr} = {hours:.2f} h ({label})")
    return "\n* Summary\n" + "\n".join(lines) + "\n"


def schedule_title(monday: _dt.date) -> str:
    """The default schedule title, e.g. ``Writing Schedule (week of ...)``."""
    return f"Writing Schedule (week of {iso_date(monday)})"


def generate_schedule(
    parsed: ParsedTable,
    week,
    config: Optional[Config] = None,
    title: Optional[str] = None,
) -> Tuple[_dt.date, str, str]:
    """Return ``(monday, title, body)`` for the schedule file.

    ``week`` is any date (or ISO string) inside the target week; it snaps to
    the Monday.  ``body`` is the full file text including the Summary section.
    """
    cfg = config or Config()
    monday = week_monday(week)
    ttl = title or schedule_title(monday)
    mapping = legend_mapping(parsed.letters, parsed.legend)
    body = build_org(parsed.events, mapping, monday, ttl, cfg) + summary(
        parsed.events, mapping
    )
    return monday, ttl, body


def schedule_filename(monday: _dt.date) -> str:
    """Return the archival file name for the week beginning ``monday``."""
    return f"writing-{iso_date(monday)}.org"
