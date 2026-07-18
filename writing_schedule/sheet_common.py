"""Shared geometry for the printable time-block sheet.

Both the ReportLab drawer and the LaTeX emitter use these helpers so the two
engines agree on which days appear, in what order, and where each block sits.
"""

from __future__ import annotations

import datetime as _dt
from typing import List, Optional, Tuple

from .config import Config
from .model import Event, ParsedTable
from .week import DAY_FULL, day_of_week, iso_date


def tidy(hhmm: str) -> str:
    """Drop a leading zero on the hour, so ``04:00`` becomes ``4:00``."""
    return hhmm[1:] if hhmm.startswith("0") else hhmm


def page_split(lo: int, hi: int) -> int:
    """Return the last hour of page one.

    Computed as ``lo + ceil(total/2) - 1`` where ``total = hi - lo + 1``,
    matching the reference.  With the defaults (4..23) this gives 13.
    """
    total = hi - lo + 1
    return lo + (total + 1) // 2 - 1


def block_rows(start: str, end: str, subrows: int) -> Tuple[int, int]:
    """Return the (start_row, end_row) grid span for a block.

    Ports the reference's row math.  A block occupies rows ``start_row`` up to
    but not including ``end_row``; the guard keeps a sub-row-short block at one
    row.
    """
    sh, sm = int(start[0:2]), int(start[3:5])
    eh, em = int(end[0:2]), int(end[3:5])
    sg = sh * subrows + min(subrows - 1, (sm * subrows) // 60)
    eg = eh * subrows + min(subrows, (em * subrows) // 60)
    if eg <= sg:
        eg = sg + 1
    return sg, eg


def block_hours(start: str, end: str) -> Tuple[float, float]:
    """Return (start, end) as fractional hours for exact canvas placement.

    An end at or before the start is treated as crossing midnight and extends
    to 24:00, so an overnight block reads as one open-ended box.
    """
    sh, sm = int(start[0:2]), int(start[3:5])
    eh, em = int(end[0:2]), int(end[3:5])
    s = sh + sm / 60.0
    e = eh + em / 60.0
    if e <= s:
        e = 24.0
    return s, e


def iter_days(
    parsed: ParsedTable, monday: _dt.date
) -> List[Tuple[_dt.date, str, List[Event]]]:
    """Return (date, "ISO (Weekday)", events) for each day column, in order."""
    offsets = sorted({off for _, off in parsed.columns})
    out = []
    for off in offsets:
        d = day_of_week(monday, off)
        date_str = f"{iso_date(d)} ({DAY_FULL[d.weekday()]})"
        events = [e for e in parsed.events if e.offset == off]
        out.append((d, date_str, events))
    return out


def key_pairs(
    parsed: ParsedTable, config: Optional[Config] = None
) -> List[Tuple[str, str]]:
    """Return (code, description) for the sheet key, using the merged legend."""
    cfg = config or Config()
    legend = dict(cfg.effective_legend(parsed.legend))
    return [(ltr, legend.get(ltr, "")) for ltr in parsed.letters]
