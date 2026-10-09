"""Write the editable week org file, one booktabs table per day.

Ports ``writing-schedule--timeblock-org-document``.  See the format spec,
"The editable week export".  Days appear in day-column order and blocks within
a day are sorted by start time; the Revision column is always empty.
"""

from __future__ import annotations

import datetime as _dt
from typing import List, Optional

from .config import Config
from .model import ParsedTable
from .overlap import conflicting_identities, event_identity
from .sheet_common import iter_days
from .week import iso_date


def _tidy(hhmm: str) -> str:
    """Drop a leading zero on the hour, so ``04:00`` becomes ``4:00``."""
    return hhmm[1:] if hhmm.startswith("0") else hhmm


def build_week_org(
    parsed: ParsedTable,
    monday: _dt.date,
    config: Optional[Config] = None,
    day: Optional[_dt.date] = None,
) -> str:
    """Return the editable org document as a string.

    By default the document covers the whole week, one section per day.  When
    ``day`` is a date, the document covers only that day, so you can edit and
    print the plan for a single day.
    """
    cfg = config or Config()
    legend = dict(cfg.effective_legend(parsed.legend))
    marked = conflicting_identities(parsed.events)

    out: List[str] = []
    if day is not None:
        title = f"Time-Block Sheet, {iso_date(day)}"
    else:
        title = f"Time-Block Sheets, week of {iso_date(monday)}"
    out.append(f"#+TITLE: {title}\n")
    out.append("#+LaTeX_HEADER: \\usepackage[margin=0.5in]{geometry}\n")
    out.append("#+OPTIONS: toc:nil\n\n")

    out.append("* Key\n")
    key_lines = []
    for ltr in parsed.letters:
        desc = legend.get(ltr, "")
        key_lines.append(f"- ={ltr}=" + (f" :: {desc}" if desc else ""))
    out.append("\n".join(key_lines))
    out.append("\n\n")

    day_blocks: List[str] = []
    for _d, date_str, evs in iter_days(parsed, monday, only=day):
        day_events = sorted(evs, key=lambda e: e.start)
        rows = ["* " + date_str]
        rows.append(f"#+CAPTION: Planned time blocks for {date_str}.")
        rows.append("#+ATTR_LATEX: :booktabs t")
        rows.append("| Time | Code | Task | Revision |")
        rows.append("|-")
        day_flagged = False
        if day_events:
            for e in day_events:
                task = legend.get(e.letter, "")
                star = "*" if event_identity(e) in marked else ""
                if star:
                    day_flagged = True
                rows.append(
                    f"| {_tidy(e.start)}-{_tidy(e.end)}{star} "
                    f"| {e.label} | {task} | |"
                )
        else:
            rows.append("| | | | |")
        block = "\n".join(rows) + "\n"
        if day_flagged:
            block += ("\nNote: a time marked with * overlaps another block "
                      "on this day.\n")
        day_blocks.append(block)

    out.append("\n".join(day_blocks))
    return "".join(out)
