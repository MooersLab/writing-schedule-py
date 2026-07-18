"""Date helpers.

These use :class:`datetime.date` rather than the reference's absolute day
numbers, which is cleaner in Python and gives the same results.  English
weekday names are emitted for predictability across machines, as the format
spec recommends.
"""

from __future__ import annotations

import datetime as _dt
from typing import Union

# English weekday names indexed by ``date.weekday()`` (Monday = 0).
DAY_ABBREV = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAY_FULL = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
]

DateLike = Union[_dt.date, str]


def to_date(value: DateLike) -> _dt.date:
    """Coerce an ISO date string or :class:`datetime.date` to a date."""
    if isinstance(value, _dt.date):
        return value
    return _dt.date.fromisoformat(value.strip())


def week_monday(value: DateLike) -> _dt.date:
    """Return the Monday on or before ``value``.

    Any day in a week therefore selects that week.
    """
    d = to_date(value)
    return d - _dt.timedelta(days=d.weekday())


def iso_date(d: _dt.date) -> str:
    """Return the ISO date string, e.g. ``2026-01-19``."""
    return d.isoformat()


def day_of_week(monday: _dt.date, offset: int) -> _dt.date:
    """Return the date ``offset`` days after ``monday``."""
    return monday + _dt.timedelta(days=offset)


def timestamp(monday: _dt.date, offset: int, start: str, end: str) -> str:
    """Build an org active timestamp for a block.

    Form: ``<YYYY-MM-DD Dow HH:MM-HH:MM>``.
    """
    d = day_of_week(monday, offset)
    return f"<{iso_date(d)} {DAY_ABBREV[d.weekday()]} {start}-{end}>"
