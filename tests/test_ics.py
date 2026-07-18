"""iCalendar exporter tests.

The reference delegates to org's exporter, so these have no ERT counterpart.
They pin the RFC 5545 subset the format spec requires: a VTIMEZONE with a
TZID, stable-shaped events, 75-octet folding, CRLF, text escaping, and the
daylight-saving guarantee that a 04:00 block stays at 04:00 local.
"""

from __future__ import annotations

import datetime as dt

from writing_schedule.config import Config
from writing_schedule.ics import build_ics, fold_line
from writing_schedule.orgtable import HLINE as H
from writing_schedule.parser import parse_table
from writing_schedule.vtimezone import build_vtimezone
from writing_schedule.week import day_of_week, week_monday

FIXED = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
MON = dt.date(2026, 1, 19)


def _small():
    table = [["Time <l>", "M", "Tu"], H, ["Gen:", "", ""],
             ["04:00-05:30", "A", "B"], H, ["A: docking", "", ""]]
    return parse_table(table)


def test_calendar_scaffold():
    ics = build_ics(_small(), MON, "My Title", calname="writing-2026-01-19")
    for token in ("BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:", "CALSCALE:GREGORIAN",
                  "X-WR-CALNAME:writing-2026-01-19", "X-WR-TIMEZONE:America/Chicago",
                  "BEGIN:VTIMEZONE", "TZID:America/Chicago", "END:VCALENDAR"):
        assert token in ics
    assert ics.count("BEGIN:VEVENT") == 2
    assert ics.endswith("\r\n")


def test_event_fields():
    ics = build_ics(_small(), MON, "T", dtstamp=FIXED)
    assert "DTSTAMP:20260101T000000Z" in ics
    assert "DTSTART;TZID=America/Chicago:20260119T040000" in ics
    assert "DTEND;TZID=America/Chicago:20260119T053000" in ics
    assert "SUMMARY:docking" in ics          # headline from the legend
    assert "DESCRIPTION:04:00-05:30" in ics
    assert "CATEGORIES:A,Gen" in ics
    assert "UID:" in ics


def test_vtimezone_has_dst_rules():
    lines = build_vtimezone("America/Chicago", 2026)
    text = "\n".join(lines)
    assert "BEGIN:DAYLIGHT" in text and "BEGIN:STANDARD" in text
    assert "TZNAME:CDT" in text and "TZNAME:CST" in text
    assert "DTSTART:20260308T020000" in text      # spring forward, 2 AM
    assert "DTSTART:20261101T020000" in text      # fall back, 2 AM
    assert "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU" in text
    assert "RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU" in text
    assert "TZOFFSETFROM:-0600" in text and "TZOFFSETTO:-0500" in text


def test_dst_week_keeps_local_time():
    mon = week_monday("2026-03-08")     # week that straddles the transition
    sun = day_of_week(mon, 6)
    assert sun == dt.date(2026, 3, 8)   # the spring-forward day
    table = [["Time <l>", "M", "Su"], H, ["Gen:", "", ""],
             ["04:00-05:30", "A", "A"]]
    ics = build_ics(parse_table(table), mon, "T", dtstamp=FIXED)
    # The block on the transition day is still at 04:00 local, not shifted.
    stamp = sun.strftime("%Y%m%d")
    assert f"DTSTART;TZID=America/Chicago:{stamp}T040000" in ics


def test_no_dst_zone_single_observance():
    lines = build_vtimezone("America/Phoenix", 2026)
    text = "\n".join(lines)
    assert text.count("BEGIN:STANDARD") == 1
    assert "BEGIN:DAYLIGHT" not in text
    assert "TZOFFSETTO:-0700" in text


def test_line_folding():
    long_desc = "review the manuscript and reconcile every figure caption " * 3
    table = [["Time <l>", "M"], H, ["04:00-05:30", "A"], H,
             [f"A: {long_desc}", ""]]
    ics = build_ics(parse_table(table), MON, "T", dtstamp=FIXED)
    # Every physical line is at most 75 octets.
    for line in ics.split("\r\n"):
        assert len(line.encode("utf-8")) <= 75
    # The long SUMMARY was actually folded (a continuation line begins with a space).
    assert "\r\n " in ics


def test_fold_line_unit():
    short = "SUMMARY:hi"
    assert fold_line(short) == short
    folded = fold_line("X" * 200)
    for piece in folded.split("\r\n"):
        assert len(piece.encode("utf-8")) <= 75


def test_text_escaping():
    table = [["Time <l>", "M"], H, ["04:00-05:30", "A"], H,
             ["A: plan, review; write", ""]]
    ics = build_ics(parse_table(table), MON, "T", dtstamp=FIXED)
    assert "SUMMARY:plan\\, review\\; write" in ics


def test_overnight_block_rolls_end_date():
    table = [["Time <l>", "M"], H, ["22:00-06:00", "A"]]
    ics = build_ics(parse_table(table), MON, "T", dtstamp=FIXED)
    assert "DTSTART;TZID=America/Chicago:20260119T220000" in ics
    assert "DTEND;TZID=America/Chicago:20260120T060000" in ics


def test_floating_fallback_without_timezone():
    cfg = Config(timezone="")
    ics = build_ics(_small(), MON, "T", cfg, dtstamp=FIXED)
    assert "BEGIN:VTIMEZONE" not in ics
    assert "X-WR-TIMEZONE" not in ics
    assert "DTSTART:20260119T040000" in ics   # no TZID parameter
