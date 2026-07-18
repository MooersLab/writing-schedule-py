"""Build an RFC 5545 VTIMEZONE component from a named zone via ``zoneinfo``.

The reference implementation writes floating local times and names the zone
only through the ``X-WR-TIMEZONE`` vendor property.  The format spec recommends
attaching an explicit ``TZID`` to each ``DTSTART``/``DTEND`` and shipping a
``VTIMEZONE`` so the times are unambiguous.  This module derives that
``VTIMEZONE`` from the standard-library ``zoneinfo`` database, so daylight
saving is correct without hard-coded offsets.

The daylight-saving transitions for the given year are located by probing the
zone, and each observance carries a ``RRULE`` derived from the transition's
month and weekday position (for example the second Sunday of March), which is
how nearly every civil zone expresses its rule.
"""

from __future__ import annotations

import datetime as _dt
from typing import List, Optional, Tuple
from zoneinfo import ZoneInfo

_UTC = _dt.timezone.utc
_BYDAY = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]


def _offset_at(tz: ZoneInfo, instant_utc: _dt.datetime) -> _dt.timedelta:
    """Return the zone's UTC offset at an absolute ``instant_utc`` (naive UTC)."""
    aware = instant_utc.replace(tzinfo=_UTC).astimezone(tz)
    return aware.utcoffset() or _dt.timedelta(0)


def _tzname_at(tz: ZoneInfo, instant_utc: _dt.datetime) -> str:
    aware = instant_utc.replace(tzinfo=_UTC).astimezone(tz)
    return aware.tzname() or "LMT"


def _fmt_offset(off: _dt.timedelta) -> str:
    total = int(off.total_seconds() // 60)
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    return f"{sign}{total // 60:02d}{total % 60:02d}"


def _find_transitions(
    tz: ZoneInfo, year: int
) -> List[Tuple[_dt.datetime, _dt.timedelta, _dt.timedelta]]:
    """Return (transition_utc, off_before, off_after) for a calendar year.

    Offsets are probed day by day (at 12:00 UTC to dodge the ambiguous hour);
    each detected change is refined to the second by bisection.
    """
    transitions = []
    probe = _dt.datetime(year, 1, 1, 12)
    prev_off = _offset_at(tz, probe)
    day = _dt.timedelta(days=1)
    end = _dt.datetime(year + 1, 1, 1, 12)
    cur = probe + day
    while cur <= end:
        off = _offset_at(tz, cur)
        if off != prev_off:
            lo, hi = cur - day, cur  # transition lies within (lo, hi]
            while (hi - lo) > _dt.timedelta(seconds=1):
                mid = lo + (hi - lo) / 2
                if _offset_at(tz, mid) == prev_off:
                    lo = mid
                else:
                    hi = mid
            transitions.append((hi, prev_off, _offset_at(tz, hi)))
            prev_off = off
        cur += day
    return transitions


def _rrule_for(local_dt: _dt.datetime) -> str:
    nth = (local_dt.day - 1) // 7 + 1
    return f"FREQ=YEARLY;BYMONTH={local_dt.month};BYDAY={nth}{_BYDAY[local_dt.weekday()]}"


def build_vtimezone(tzname: str, year: int) -> Optional[List[str]]:
    """Return the VTIMEZONE as unfolded content lines, or None if unavailable."""
    try:
        tz = ZoneInfo(tzname)
    except Exception:
        return None

    lines = ["BEGIN:VTIMEZONE", f"TZID:{tzname}"]
    transitions = _find_transitions(tz, year)

    if not transitions:
        # No daylight saving: one STANDARD observance with the constant offset.
        off = _offset_at(tz, _dt.datetime(year, 1, 1, 12))
        lines += [
            "BEGIN:STANDARD",
            f"TZOFFSETFROM:{_fmt_offset(off)}",
            f"TZOFFSETTO:{_fmt_offset(off)}",
            f"TZNAME:{_tzname_at(tz, _dt.datetime(year, 1, 1, 12))}",
            "DTSTART:19700101T000000",
            "END:STANDARD",
        ]
    else:
        for t_utc, off_before, off_after in transitions:
            # Onset in local wall time, interpreted against the prior offset.
            local = t_utc + off_before
            kind = "DAYLIGHT" if off_after > off_before else "STANDARD"
            lines += [
                f"BEGIN:{kind}",
                f"TZOFFSETFROM:{_fmt_offset(off_before)}",
                f"TZOFFSETTO:{_fmt_offset(off_after)}",
                f"TZNAME:{_tzname_at(tz, t_utc)}",
                f"DTSTART:{local.strftime('%Y%m%dT%H%M%S')}",
                f"RRULE:{_rrule_for(local)}",
                f"END:{kind}",
            ]

    lines.append("END:VTIMEZONE")
    return lines
