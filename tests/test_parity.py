"""Parity test against the canonical fixture examples/projects-and-tasks.org.

This is the shared contract from the plan's suggested first step: the parser
must find forty-four events with the correct codes, offsets, and times.  The
remaining assertions run the full pipeline end to end on the same fixture.
"""

from __future__ import annotations

import datetime as dt

from writing_schedule.ics import build_ics
from writing_schedule.parser import parse_text
from writing_schedule.schedule import generate_schedule
from writing_schedule.sheet import render_week_pdf
from writing_schedule.sheet_org import build_week_org

EXPECTED_LETTERS = [
    "A", "B", "CE", "CM", "EM", "EX", "LC", "LP", "RT", "TP", "TT", "W",
]


def test_parser_finds_forty_four_events(projects_and_tasks_text):
    parsed = parse_text(projects_and_tasks_text)
    assert len(parsed.events) == 44
    assert parsed.letters == EXPECTED_LETTERS
    assert len(parsed.letters) == 12


def test_legend_describes_every_code(projects_and_tasks_text):
    parsed = parse_text(projects_and_tasks_text)
    for code in EXPECTED_LETTERS:
        assert parsed.legend_lookup(code), f"missing legend for {code}"
    assert parsed.legend_lookup("EM") == "email"
    assert parsed.legend_lookup("W") == "2026words"
    assert parsed.legend_lookup("RT") == "required training"


def test_first_and_multiletter_events(projects_and_tasks_text):
    parsed = parse_text(projects_and_tasks_text)
    first = parsed.events[0]
    assert (first.section, first.offset, first.start, first.end, first.letter) == (
        "Generative", 0, "04:00", "05:30", "A",
    )
    # The 08:15-08:45 CM commute block is a two-letter code under Supporting.
    cm = [e for e in parsed.events if e.letter == "CM"]
    assert len(cm) == 5
    assert all(e.section == "Supporting" and e.start == "08:15" for e in cm)


def test_full_pipeline_runs(projects_and_tasks_text, tmp_path):
    parsed = parse_text(projects_and_tasks_text)
    monday, title, body = generate_schedule(parsed, "2026-01-19")
    assert monday == dt.date(2026, 1, 19)
    # Sections appear in first-occurrence order.
    assert body.index("* Generative") < body.index("* Rewriting") < body.index("* Supporting")

    ics = build_ics(parsed, monday, title)
    assert ics.count("BEGIN:VEVENT") == 44

    week_org = build_week_org(parsed, monday)
    for iso in ("2026-01-19", "2026-01-20", "2026-01-24"):
        assert f"* {iso}" in week_org

    pdf = str(tmp_path / "sheets.pdf")
    render_week_pdf(parsed, monday, pdf)
    import os
    assert os.path.getsize(pdf) > 0
