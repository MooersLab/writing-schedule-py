"""Detect overlapping time blocks within a single day.

The weekly table places generative, editing, and support writing activities in
separate row groups, so the same day can carry a block in one group and a
clashing block in another without the writer noticing.  This module finds such
clashes so the command line and the Emacs commands can warn about them.

Semantics, shared with ``writing-schedule.el``:

- Each filled block becomes a half-open minute interval ``[start, end)`` on its
  own day.  When ``end <= start`` the block runs past midnight, so the end
  gains 1440 minutes, keeping the interval a positive length.
- Two blocks on the *same* day conflict when ``start_a < end_b`` and
  ``start_b < end_a``.  Half-open intervals mean two blocks that merely touch,
  for example 04:00-05:30 then 05:30-07:00, do not conflict.  Two identical
  blocks on the same day do conflict, because that is the common mistake.
- Blocks on different days never conflict.  The after-midnight tail of an
  overnight block does not count against the next day, because comparison is
  same-day only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Set, Tuple

from .model import Event
from .week import DAY_FULL

# An event identity used to mark a block on a printed sheet.  It is the tuple
# that uniquely names a block within a table.
Identity = Tuple[int, str, str, str, str]


def _minutes(hhmm: str) -> int:
    return 60 * int(hhmm[0:2]) + int(hhmm[3:5])


def _interval(ev: Event) -> Tuple[int, int]:
    """Return the half-open ``[start, end)`` minute interval for ``ev``."""
    start = _minutes(ev.start)
    end = _minutes(ev.end)
    if end <= start:
        end += 1440
    return start, end


def event_identity(ev: Event) -> Identity:
    """Return the identity tuple naming ``ev`` within a table."""
    return (ev.offset, ev.start, ev.end, ev.letter, ev.section)


@dataclass(frozen=True)
class Overlap:
    """One conflicting pair of blocks on one day.

    ``offset`` is the day (0 = Monday).  ``first`` starts no later than
    ``second`` in the sorted day order.
    """

    offset: int
    first: Event
    second: Event


def find_overlaps(events: List[Event]) -> List[Overlap]:
    """Return every conflicting pair of blocks, grouped and ordered by day.

    Within a day the events are sorted by start minute, so the output order is
    stable and the ``first`` block of each pair starts no later than the
    ``second``.
    """
    by_day: dict = {}
    for ev in events:
        by_day.setdefault(ev.offset, []).append(ev)

    conflicts: List[Overlap] = []
    for offset in sorted(by_day):
        day_events = sorted(
            by_day[offset],
            key=lambda e: (_interval(e)[0], _interval(e)[1], e.letter, e.section),
        )
        intervals = [_interval(e) for e in day_events]
        n = len(day_events)
        for i in range(n):
            si, ei = intervals[i]
            for j in range(i + 1, n):
                sj, ej = intervals[j]
                if sj >= ei:
                    # Sorted by start, so no later block can overlap block i.
                    break
                if si < ej and sj < ei:
                    conflicts.append(Overlap(offset, day_events[i], day_events[j]))
    return conflicts


def _format_block(ev: Event) -> str:
    return f"{ev.start}-{ev.end} [{ev.letter}, {ev.section}]"


def overlap_lines(conflicts: List[Overlap]) -> List[str]:
    """Return one human readable line per conflict, keyed by weekday name."""
    return [
        f"{DAY_FULL[c.offset]}: {_format_block(c.first)} "
        f"overlaps {_format_block(c.second)}"
        for c in conflicts
    ]


def conflicting_identities(events: List[Event]) -> Set[Identity]:
    """Return the identities of every block that takes part in a clash.

    A sheet builder uses this set to mark the offending blocks.
    """
    ids: Set[Identity] = set()
    for c in find_overlaps(events):
        ids.add(event_identity(c.first))
        ids.add(event_identity(c.second))
    return ids
