"""Pytest port of test/test-writing-schedule.el (the ERT suite).

Test names mirror the ERT test names so the two suites read side by side:
an ERT test ``writing-schedule/parse/first-event-fields`` becomes
``test_parse__first_event_fields`` here.  Each test's docstring quotes the
original ERT name.

A handful of ERT tests exercise Emacs-only mechanisms that the Python port
does not reproduce, and are intentionally not ported:

  - writing-schedule/week-file-regexp/*      (custom file-format token regexp)
  - writing-schedule/ordered-table/*         (Emacs completion metadata)
  - writing-schedule/table-file-for-week/*   (tables/ working-copy workflow)
  - writing-schedule/directory-accessors/*   (defcustom directory derivation)
  - writing-schedule/timeblock/sheets-directory (same; Python uses --dir)
  - writing-schedule/command-map/*           (Emacs keymap)

The archive behaviour those regexp tests supported is covered by
``test_archived_weeks__lists_newest_first``.
"""

from __future__ import annotations

import datetime as dt

import pytest

from writing_schedule.archive import archived_weeks
from writing_schedule.config import Config
from writing_schedule.model import Event, MapEntry, map_get
from writing_schedule.orgtable import HLINE as H
from writing_schedule.parser import (
    day_offset,
    minutes_between,
    parse_table,
    parse_time,
)
from writing_schedule.schedule import build_org, legend_mapping, schedule_filename, summary
from writing_schedule.sheet_common import block_rows
from writing_schedule.sheet_latex import _colspec, _spans, latex_escape
from writing_schedule.sheet_org import build_week_org
from writing_schedule.template import _blank_row, template_string
from writing_schedule.week import iso_date, timestamp, week_monday

MON = dt.date(2026, 1, 19)  # a Monday


# --- writing-schedule--day-offset -------------------------------------------

def test_day_offset__known_abbreviations():
    """writing-schedule/day-offset/known-abbreviations"""
    cases = {
        "M": 0, "Mo": 0, "Mon": 0, "mon": 0,
        "Tu": 1, "tue": 1,
        "W": 2, "We": 2, "Wed": 2,
        "Th": 3, "thu": 3,
        "F": 4, "Fr": 4, "Fri": 4,
        "Sa": 5, "sat": 5,
        "Su": 6, "Sun": 6,
    }
    for cell, off in cases.items():
        assert day_offset(cell) == off


def test_day_offset__trims_whitespace():
    """writing-schedule/day-offset/trims-whitespace"""
    assert day_offset("  M  ") == 0


def test_day_offset__rejects_unknown():
    """writing-schedule/day-offset/rejects-unknown"""
    assert day_offset("X") is None
    assert day_offset("") is None
    assert day_offset(None) is None
    # A lone T is ambiguous between Tuesday and Thursday, so it is excluded.
    assert day_offset("T") is None


# --- writing-schedule--parse-time -------------------------------------------

def test_parse_time__happy_path():
    """writing-schedule/parse-time/happy-path"""
    assert parse_time("04:00-05:30") == ("04:00", "05:30")
    assert parse_time("20:30-22:00") == ("20:30", "22:00")


def test_parse_time__zero_pads_single_digit_hour():
    """writing-schedule/parse-time/zero-pads-single-digit-hour"""
    assert parse_time("9:15 - 10:45") == ("09:15", "10:45")
    assert parse_time("04:00-5:30") == ("04:00", "05:30")


def test_parse_time__tolerates_irregular_spacing():
    """writing-schedule/parse-time/tolerates-irregular-spacing"""
    assert parse_time("15:00- 16:30") == ("15:00", "16:30")
    assert parse_time("11:30 - 13:00") == ("11:30", "13:00")


def test_parse_time__rejects_non_times():
    """writing-schedule/parse-time/rejects-non-times"""
    assert parse_time("Generative:") is None
    assert parse_time("") is None
    assert parse_time(None) is None


def test_parse_time__tolerates_space_after_colon():
    """writing-schedule/parse-time/tolerates-space-after-colon"""
    assert parse_time("15:00-16: 30") == ("15:00", "16:30")
    assert parse_time("9: 15 - 10:45") == ("09:15", "10:45")


# --- writing-schedule--minutes ----------------------------------------------

def test_minutes__various_durations():
    """writing-schedule/minutes/various-durations"""
    assert minutes_between("04:00", "05:30") == 90
    assert minutes_between("09:15", "10:45") == 90
    assert minutes_between("04:00", "05:00") == 60
    assert minutes_between("04:00", "04:15") == 15


def test_minutes__zero_duration():
    """writing-schedule/minutes/zero-duration"""
    assert minutes_between("00:00", "00:00") == 0


# --- writing-schedule--parse ------------------------------------------------

def test_parse__reads_events_letters_legend():
    """writing-schedule/parse/reads-events-letters-legend"""
    table = [
        ["Time <l>", "M", "Tu", "W"], H,
        ["Gen:", "", "", ""],
        ["04:00-05:30", "A", "B", ""],
        ["05:45-07:15", "", "a", "B"], H,
        ["Support", "", "", ""],
        ["13:15-14:45", "A", "", ""], H,
        ["A:", "Proj Alpha", "", ""],
        ["B:", "Proj Beta", "", ""],
        ["C: Gamma inline", "", "", ""],
    ]
    parsed = parse_table(table)
    assert len(parsed.events) == 5
    assert parsed.letters == ["A", "B"]
    assert parsed.legend_lookup("A") == "Proj Alpha"
    assert parsed.legend_lookup("B") == "Proj Beta"
    assert parsed.legend_lookup("C") == "Gamma inline"


def test_parse__first_event_fields():
    """writing-schedule/parse/first-event-fields"""
    table = [["Time <l>", "M", "Tu", "W"], H, ["Gen:", "", "", ""],
             ["04:00-05:30", "A", "B", ""]]
    ev = parse_table(table).events[0]
    assert ev.section == "Gen"
    assert ev.offset == 0
    assert ev.start == "04:00"
    assert ev.end == "05:30"
    assert ev.letter == "A"


def test_parse__uppercases_letters():
    """writing-schedule/parse/uppercases-letters"""
    table = [["Time <l>", "M"], H, ["Gen:", ""], ["04:00-05:30", "a"]]
    assert parse_table(table).events[0].letter == "A"


def test_parse__legend_description_in_first_column():
    """writing-schedule/parse/legend-description-in-first-column"""
    table = [["Time <l>", "M"], H, ["Gen:", ""], ["04:00-05:30", "A"], H,
             ["A:0211dnph1docking", ""], ["B: DUSP1 radiation", ""]]
    parsed = parse_table(table)
    assert parsed.legend_lookup("A") == "0211dnph1docking"
    assert parsed.legend_lookup("B") == "DUSP1 radiation"


def test_parse__two_letter_codes_and_many_projects():
    """writing-schedule/parse/two-letter-codes-and-many-projects"""
    table = [
        ["Time <l>", "M", "Tu", "W"], H,
        ["Generative:", "", "", ""],
        ["04:00-05:30", "A", "EM", "W"],
        ["05:45-07:15", "B", "EX", "TT"], H,
        ["A: DNPH1 docking", "", "", ""],
        ["B: DUSP1 radiation", "", "", ""],
        ["EM: email", "", "", ""],
        ["EX: exercise", "", "", ""],
        ["W: 2026words", "", "", ""],
        ["TT: time tracking", "", "", ""],
    ]
    parsed = parse_table(table)
    assert parsed.letters == ["A", "B", "EM", "EX", "TT", "W"]
    assert parsed.legend_lookup("EM") == "email"
    assert parsed.legend_lookup("W") == "2026words"
    assert parsed.legend_lookup("TT") == "time tracking"
    assert parsed.legend_lookup("GENERATIVE") is None


def test_parse__legend_code_is_case_sensitive():
    """writing-schedule/parse/legend-code-is-case-sensitive"""
    table = [["Time <l>", "M"], H, ["Gen:", ""], ["04:00-05:30", "EM"], H,
             ["EM: email", ""]]
    parsed = parse_table(table)
    assert parsed.legend_lookup("EM") == "email"
    assert parsed.legend_lookup("GEN") is None
    assert parsed.events[0].section == "Gen"


def test_parse__section_without_colon():
    """writing-schedule/parse/section-without-colon"""
    table = [["Time <l>", "M"], H, ["Support", ""], ["13:15-14:45", "A"]]
    assert parse_table(table).events[0].section == "Support"


def test_parse__header_only_has_no_events():
    """writing-schedule/parse/header-only-has-no-events"""
    assert parse_table([["Time", "M", "Tu"], H]).events == []


# --- writing-schedule--week-monday ------------------------------------------

def test_week_monday__snaps_any_day_to_monday():
    """writing-schedule/week-monday/snaps-any-day-to-monday"""
    for day in ("2026-01-19", "2026-01-20", "2026-01-24", "2026-01-25"):
        assert week_monday(day) == dt.date(2026, 1, 19)


# --- writing-schedule--iso-date and file-for-week ---------------------------

def test_iso_date__formats_date():
    """writing-schedule/iso-date/formats-absolute-date"""
    assert iso_date(dt.date(2026, 1, 19)) == "2026-01-19"


def test_file_for_week__builds_dated_name():
    """writing-schedule/file-for-week/builds-dated-path"""
    assert schedule_filename(dt.date(2026, 1, 19)) == "writing-2026-01-19.org"


# --- writing-schedule--timestamp --------------------------------------------

def test_timestamp__formats_active_range():
    """writing-schedule/timestamp/formats-active-range"""
    assert timestamp(MON, 0, "04:00", "05:30") == "<2026-01-19 Mon 04:00-05:30>"
    assert timestamp(MON, 5, "20:30", "22:00") == "<2026-01-24 Sat 20:30-22:00>"


# --- writing-schedule--map-get ----------------------------------------------

def test_map_get__finds_and_misses():
    """writing-schedule/map-get/finds-and-misses"""
    mapping = [MapEntry("A", "1"), MapEntry("B", "2")]
    assert map_get(mapping, "B").code == "2"
    assert map_get(mapping, "Z") is None


# --- writing-schedule--blank-row --------------------------------------------

def test_blank_row__builds_cells():
    """writing-schedule/blank-row/builds-cells"""
    assert _blank_row("A:", 6) == "| A: |  |  |  |  |  |  |\n"
    assert _blank_row("X", 1) == "| X |  |\n"


# --- writing-schedule--build-org --------------------------------------------

def test_build_org__contains_expected_structure():
    """writing-schedule/build-org/contains-expected-structure"""
    events = [Event("Gen", 0, "04:00", "05:30", "A"),
              Event("Gen", 1, "04:00", "05:30", "B")]
    mapping = [MapEntry("A", "100", "Alpha"), MapEntry("B", "200", "Beta")]
    org = build_org(events, mapping, MON, "My Title")
    assert "#+TITLE: My Title" in org
    assert "usepackage[margin=0.5in]{geometry}" in org
    assert "\n* Gen\n" in org
    assert ":CATEGORY: Gen" in org
    assert "** TODO Alpha :A:" in org
    assert ":WS_CODE: 100" in org
    assert "<2026-01-19 Mon 04:00-05:30>" in org
    assert "<2026-01-20 Tue 04:00-05:30>" in org


def test_build_org__honours_use_todo_nil():
    """writing-schedule/build-org/honours-use-todo-nil"""
    events = [Event("Gen", 0, "04:00", "05:30", "A")]
    mapping = [MapEntry("A", "100", "Alpha")]
    org = build_org(events, mapping, MON, "T", Config(use_todo=False))
    assert "** Alpha :A:\n" in org
    assert "TODO" not in org


def test_build_org__head_falls_back_to_code_then_letter():
    """writing-schedule/build-org/head-falls-back-to-code-then-letter"""
    events = [Event("Gen", 0, "04:00", "05:30", "A"),
              Event("Gen", 1, "04:00", "05:30", "C")]
    mapping = [MapEntry("A", "77", "")]
    org = build_org(events, mapping, MON, "T")
    assert "** TODO 77 :A:" in org
    assert "** TODO Project C :C:" in org


# --- writing-schedule--summary ----------------------------------------------

def test_summary__totals_hours_per_letter():
    """writing-schedule/summary/totals-hours-per-letter"""
    events = [Event("Gen", 0, "04:00", "05:30", "A"),
              Event("Gen", 1, "04:00", "05:30", "A")]
    mapping = [MapEntry("A", "100", "Alpha")]
    s = summary(events, mapping)
    assert "* Summary" in s
    assert "- A = 3.00 h (Alpha)" in s


def test_summary__label_falls_back_to_code_then_letter():
    """writing-schedule/summary/label-falls-back-to-code-then-letter"""
    events = [Event("Gen", 0, "04:00", "05:30", "A"),
              Event("Gen", 1, "04:00", "05:30", "C")]
    mapping = [MapEntry("A", "77", "")]
    s = summary(events, mapping)
    assert "- A = 1.50 h (77)" in s
    assert "- C = 1.50 h (Project C)" in s


# --- writing-schedule--template-string --------------------------------------

def test_template_string__builds_n_projects():
    """writing-schedule/template-string/builds-n-projects"""
    s = template_string(3)
    assert "#+TITLE: Writing Schedule for 3 Projects" in s
    assert "Time <l>" in s
    assert "| A: |" in s
    assert "| C: |" in s
    assert "| D: |" not in s
    assert "for 1 Project\n" in template_string(0)
    assert "for 9 Projects" in template_string("9")
    assert "for 26 Projects" in template_string(99)


def test_template_string__more_than_four():
    """writing-schedule/template-string/more-than-four"""
    s = template_string(6)
    assert "| E: |" in s
    assert "| F: |" in s
    assert "| G: |" not in s


# --- writing-schedule--timeblock (LaTeX + org + effective legend) -----------

def test_timeblock__custom_code_descriptions():
    """writing-schedule/timeblock/custom-code-descriptions"""
    cfg = Config(code_descriptions={"Z": "zebra", "A": "ignored"})
    eff = dict(cfg.effective_legend([("A", "docking")]))
    assert eff["A"] == "docking"
    assert eff["Z"] == "zebra"

    table = [["Time <l>", "M"], H, ["04:00-05:30", "Z"]]
    parsed = parse_table(table)
    from writing_schedule.sheet_latex import render_latex
    doc = render_latex(parsed, MON, cfg)
    assert "Z = zebra" in doc

    # With no custom descriptions the legend is unchanged.
    assert Config().effective_legend([("A", "docking")]) == [("A", "docking")]


def test_timeblock__colspec():
    """writing-schedule/timeblock/colspec"""
    assert _colspec(4) == "|m{1cm}:m{4cm}:m{4cm}:m{4cm}:m{4cm}|"
    assert _colspec(1) == "|m{1cm}:m{4cm}|"


def test_timeblock__latex_escape():
    """writing-schedule/timeblock/latex-escape"""
    assert latex_escape("a & b_c 50%") == "a \\& b\\_c 50\\%"
    assert latex_escape(None) == ""


def test_timeblock__spans_cover_the_range():
    """writing-schedule/timeblock/spans-cover-the-range"""
    spans = _spans([Event("Gen", 0, "04:00", "05:30", "A")], 5)
    s0, s1, label = spans[0]
    assert s0 == 20
    assert s1 == 27
    assert label.startswith("A")
    short = _spans([Event("Gen", 0, "04:00", "04:10", "X")], 5)[0]
    assert short[1] == short[0] + 1
    # The same math is available as sheet_common.block_rows.
    assert block_rows("04:00", "05:30", 5) == (20, 27)
    assert block_rows("04:00", "04:10", 5) == (20, 21)


def test_timeblock__document_has_block_outline():
    """writing-schedule/timeblock/document-has-block-outline"""
    from writing_schedule.sheet_latex import render_latex
    table = [["Time <l>", "M"], H, ["04:00-05:30", "A"], H, ["A: docking", ""]]
    doc = render_latex(parse_table(table), MON)
    assert "cmidrule[1pt]{2-2}" in doc
    assert "vrule width 1pt" in doc
    assert "4:00-5:30" in doc


def test_timeblock__document_content():
    """writing-schedule/timeblock/document-content"""
    from writing_schedule.sheet_latex import render_latex
    table = [["Time <l>", "M", "Tu"], H, ["Gen:", "", ""],
             ["04:00-05:30", "A", "EM"], H,
             ["A: docking", "", ""], ["EM: email", "", ""]]
    doc = render_latex(parse_table(table), MON)
    assert "A = docking" in doc
    assert "EM = email" in doc
    assert "Date: 2026-01-19 (Monday)" in doc
    assert "Date: 2026-01-20 (Tuesday)" in doc
    assert "4:00-5:30" in doc
    assert "\\newpage" in doc
    assert "\\clearpage" in doc
    assert "\\documentclass{article}" in doc


def test_timeblock__org_document():
    """writing-schedule/timeblock/org-document"""
    table = [["Time <l>", "M", "Tu"], H, ["04:00-05:30", "A", "EM"], H,
             ["A: docking", "", ""], ["EM: email", "", ""]]
    org = build_week_org(parse_table(table), MON)
    assert "#+TITLE: Time-Block Sheets, week of 2026-01-19" in org
    assert "usepackage[margin=0.5in]{geometry}" in org
    assert "=A= :: docking" in org
    assert "\n* 2026-01-19 (Monday)" in org
    assert "\n* 2026-01-20 (Tuesday)" in org
    assert ":booktabs t" in org
    assert "| Time | Code | Task | Revision |" in org
    assert "| 4:00-5:30 | A | docking | |" in org


# --- writing-schedule--legend-mapping ---------------------------------------

def test_legend_mapping__uses_legend_descriptions():
    """writing-schedule/legend-mapping/uses-legend-descriptions"""
    mapping = legend_mapping(["A", "B"], [("A", "Alpha"), ("C", "Gamma")])
    assert mapping[0].letter == "A"
    assert mapping[0].desc == "Alpha"
    assert mapping[0].code == ""
    assert mapping[1].desc == ""


# --- archive (covers the intent of the ERT week-file-regexp tests) ----------

def test_archived_weeks__lists_newest_first(tmp_path):
    """writing-schedule/archived-weeks/lists-newest-first"""
    for d in ("2026-01-19", "2026-02-02", "2026-01-26"):
        (tmp_path / f"writing-{d}.org").write_text("x")
    (tmp_path / "writing-2026-01-19.ics").write_text("x")  # decoys, ignored
    (tmp_path / "notes.org").write_text("x")
    weeks = archived_weeks(str(tmp_path))
    assert [iso for iso, _ in weeks] == ["2026-02-02", "2026-01-26", "2026-01-19"]
    assert weeks[0][1].endswith("writing-2026-02-02.org")
