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
from .week import DAY_FULL, day_of_week, iso_date


def _tidy(hhmm: str) -> str:
    """Drop a leading zero on the hour, so ``04:00`` becomes ``4:00``."""
    return hhmm[1:] if hhmm.startswith("0") else hhmm


def build_week_org(
    parsed: ParsedTable, monday: _dt.date, config: Optional[Config] = None
) -> str:
    """Return the editable week org document as a string."""
    cfg = config or Config()
    legend = dict(cfg.effective_legend(parsed.legend))
    offsets = sorted({off for _, off in parsed.columns})

    out: List[str] = []
    out.append(f"#+TITLE: Time-Block Sheets, week of {iso_date(monday)}\n")
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
    for off in offsets:
        d = day_of_week(monday, off)
        date_str = f"{iso_date(d)} ({DAY_FULL[d.weekday()]})"
        day_events = sorted(
            (e for e in parsed.events if e.offset == off),
            key=lambda e: e.start,
        )
        rows = ["* " + date_str]
        rows.append(f"#+CAPTION: Planned time blocks for {date_str}.")
        rows.append("#+ATTR_LATEX: :booktabs t")
        rows.append("| Time | Code | Task | Revision |")
        rows.append("|-")
        if day_events:
            for e in day_events:
                task = legend.get(e.letter, "")
                rows.append(
                    f"| {_tidy(e.start)}-{_tidy(e.end)} | {e.letter} | {task} | |"
                )
        else:
            rows.append("| | | | |")
        day_blocks.append("\n".join(rows) + "\n")

    out.append("\n".join(day_blocks))
    return "".join(out)
