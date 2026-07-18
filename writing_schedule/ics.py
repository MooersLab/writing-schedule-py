"""Emit an iCalendar (RFC 5545) file directly, without a third-party library.

The reference implementation hands the generated org file to org's own
exporter.  A second implementation is expected to write the small required
subset itself, because a dependency-free program is easier to install.  This
module produces one ``VEVENT`` per block, wrapped in a ``VCALENDAR`` with a
``VTIMEZONE`` built from ``zoneinfo`` (see :mod:`writing_schedule.vtimezone`).

Times are written as local wall-clock values with a ``TZID`` parameter, so a
04:00 block stays at 04:00 in every week, and the ``VTIMEZONE`` supplies the
offset a client needs to compute the absolute instant.  When no zone is
configured the exporter falls back to the reference's floating-time behaviour.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
from typing import List, Optional

from .config import Config
from .model import Event, ParsedTable, map_get
from .schedule import _headline, legend_mapping
from .vtimezone import build_vtimezone
from .week import day_of_week, iso_date


def _escape(text: str) -> str:
    """Escape a TEXT value per RFC 5545 (backslash, semicolon, comma, newline)."""
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def fold_line(line: str) -> str:
    """Fold a content line at 75 octets with CRLF + single-space continuation."""
    raw = line.encode("utf-8")
    if len(raw) <= 75:
        return line
    pieces = []
    start = 0
    limit = 75
    while start < len(raw):
        end = min(start + limit, len(raw))
        # Do not split a multi-byte UTF-8 sequence.
        while end < len(raw) and (raw[end] & 0xC0) == 0x80:
            end -= 1
        pieces.append(raw[start:end])
        start = end
        limit = 74  # continuation lines start with a space, leaving 74 octets
    return "\r\n ".join(p.decode("utf-8") for p in pieces)


def _hhmmss(hhmm: str) -> str:
    return hhmm.replace(":", "") + "00"


def _uid(iso: str, start: str, end: str, letter: str, section: str, n: int) -> str:
    key = f"{iso}|{start}|{end}|{letter}|{section}|{n}"
    digest = hashlib.md5(key.encode("utf-8")).hexdigest()[:20]
    return f"{digest}@writing-schedule.py"


def build_ics(
    parsed: ParsedTable,
    monday: _dt.date,
    title: str,
    config: Optional[Config] = None,
    calname: Optional[str] = None,
    dtstamp: Optional[_dt.datetime] = None,
) -> str:
    """Return the iCalendar text for ``parsed`` anchored at ``monday``.

    ``dtstamp`` may be supplied for reproducible output; it defaults to the
    current time in UTC.
    """
    cfg = config or Config()
    mapping = legend_mapping(parsed.letters, parsed.legend)
    if dtstamp is None:
        dtstamp = _dt.datetime.now(_dt.timezone.utc)
    stamp = dtstamp.astimezone(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    tzid = cfg.timezone.strip()
    vtz = build_vtimezone(tzid, monday.year) if tzid else None
    use_tzid = vtz is not None

    lines: List[str] = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{cfg.prodid}",
        "CALSCALE:GREGORIAN",
    ]
    if calname:
        lines.append(f"X-WR-CALNAME:{_escape(calname)}")
    if tzid:
        lines.append(f"X-WR-TIMEZONE:{tzid}")
    lines.append(f"X-WR-CALDESC:{_escape(title)}")
    if vtz:
        lines.extend(vtz)

    # Duplicate-key counter so identical blocks still get distinct UIDs.
    seen: dict = {}
    for ev in parsed.events:
        d = day_of_week(monday, ev.offset)
        iso = iso_date(d)
        key = (iso, ev.start, ev.end, ev.letter, ev.section)
        n = seen.get(key, 0)
        seen[key] = n + 1

        # Overnight block: roll the end to the next day.
        end_date = d
        if ev.end <= ev.start:
            end_date = d + _dt.timedelta(days=1)

        entry = map_get(mapping, ev.letter)
        summary = _headline(entry, ev.letter)
        categories = f"{_escape(ev.letter)},{_escape(ev.section)}"

        if use_tzid:
            dtstart = f"DTSTART;TZID={tzid}:{iso.replace('-', '')}T{_hhmmss(ev.start)}"
            dtend = f"DTEND;TZID={tzid}:{iso_date(end_date).replace('-', '')}T{_hhmmss(ev.end)}"
        else:
            dtstart = f"DTSTART:{iso.replace('-', '')}T{_hhmmss(ev.start)}"
            dtend = f"DTEND:{iso_date(end_date).replace('-', '')}T{_hhmmss(ev.end)}"

        lines += [
            "BEGIN:VEVENT",
            f"UID:{_uid(iso, ev.start, ev.end, ev.letter, ev.section, n)}",
            f"DTSTAMP:{stamp}",
            dtstart,
            dtend,
            f"SUMMARY:{_escape(summary)}",
            f"DESCRIPTION:{_escape(ev.start + '-' + ev.end)}",
            f"CATEGORIES:{categories}",
            "END:VEVENT",
        ]

    lines.append("END:VCALENDAR")
    return "\r\n".join(fold_line(ln) for ln in lines) + "\r\n"
