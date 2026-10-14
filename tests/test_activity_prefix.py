"""Activity letters in the day cells, legend default activities, and starter days.

A cell may carry its activity as a lowercase letter before the code, so ``gA``
is generative work on project A.  A legend entry may name a default activity
with a tag such as ``@support``.  Both resolve to the section name a header
would have given, so every consumer of ``Event.section`` keeps working.
"""

from __future__ import annotations

import pytest

from writing_schedule.ics import build_ics
from writing_schedule.overlap import find_overlaps
from writing_schedule.parser import (parse_text, split_cell,
                                     split_legend_activity)
from writing_schedule.template import template_string

FREE = (
    "| Time        | M  | Tu | W  |\n"
    "|-------------+----+----+----|\n"
    "| 12:15-13:00 | sE | E  | sE |\n"
    "| 17:30-19:00 | eB | eA |    |\n"
    "| 21:00-23:30 | gA | gB | ga |\n"
    "|-------------+----+----+----|\n"
    "| A: DNPH1 docking :safe: |  |  |  |\n"
    "| B: DUSP1 radiation |  |  |  |\n"
    "| E: email @support |  |  |  |\n"
)

SECTIONED = (
    "| Time        | M  | Tu |\n"
    "|-------------+----+----|\n"
    "| Generative: |    |    |\n"
    "| 04:00-05:30 | A  | eA |\n"
    "| 05:45-07:15 | T  | B  |\n"
    "|-------------+----+----|\n"
    "| A: one |  |  |\n"
    "| B: two |  |  |\n"
    "| T: teaching @support |  |  |\n"
    "| T: teaching again @editing |  |  |\n"
)


def _by(parsed):
    return {(e.offset, e.start, e.letter): e.section for e in parsed.events}


@pytest.mark.parametrize("cell, expected", [
    ("gA", ("g", "A")), ("eEM", ("e", "EM")), ("sW2", ("s", "W2")),
    ("A", (None, "A")), ("ga", (None, "GA")), ("gem", (None, "GEM")),
    (" sE ", ("s", "E")), ("xA", (None, "XA")), ("", (None, "")),
])
def test_split_cell(cell, expected):
    assert split_cell(cell) == expected


@pytest.mark.parametrize("desc, expected", [
    ("email @support", ("email", "support")),
    ("@editing paper", ("paper", "editing")),
    ("paper @Generative :safe:", ("paper :safe:", "generative")),
    ("me@support.org", ("me@support.org", None)),
    ("plain", ("plain", None)),
])
def test_split_legend_activity(desc, expected):
    assert split_legend_activity(desc) == expected


def test_a_prefix_names_the_activity_without_any_header():
    parsed = parse_text(FREE)
    by = _by(parsed)
    assert by[(0, "12:15", "E")] == "Supporting"
    assert by[(0, "17:30", "B")] == "Rewriting"
    assert by[(0, "21:00", "A")] == "Generative"


def test_the_code_is_stored_without_the_prefix():
    parsed = parse_text(FREE)
    assert parsed.letters == ["A", "B", "E", "GA"]
    assert {e.letter for e in parsed.events} == {"A", "B", "E", "GA"}


def test_a_legend_default_fills_a_bare_code():
    by = _by(parse_text(FREE))
    assert by[(1, "12:15", "E")] == "Supporting"


def test_a_bare_code_with_no_default_or_header_is_writing():
    by = _by(parse_text(FREE))
    assert by[(2, "21:00", "GA")] == "Writing"


def test_the_tag_is_stripped_from_the_description():
    parsed = parse_text(FREE)
    assert parsed.legend_lookup("E") == "email"
    assert parsed.legend_lookup("A") == "DNPH1 docking :safe:"


def test_the_order_is_prefix_then_default_then_header():
    by = _by(parse_text(SECTIONED))
    assert by[(0, "04:00", "A")] == "Generative"     # the header
    assert by[(1, "04:00", "A")] == "Rewriting"      # the prefix beats it
    assert by[(0, "05:45", "T")] == "Supporting"     # the default beats it


def test_the_first_legend_definition_decides_the_default():
    by = _by(parse_text(SECTIONED))
    assert by[(0, "05:45", "T")] == "Supporting"


def test_a_table_without_prefixes_parses_as_before(projects_and_tasks_text):
    parsed = parse_text(projects_and_tasks_text)
    assert len(parsed.events) == 44
    assert {e.section for e in parsed.events} <= {
        "Generative", "Rewriting", "Supporting", "Writing"}


def test_the_calendar_carries_the_resolved_activity():
    import datetime as dt
    from writing_schedule.config import Config
    text = build_ics(parse_text(FREE), dt.date(2026, 1, 19), "week",
                     config=Config(timezone=""))
    assert "CATEGORIES:E,Supporting" in text
    assert "CATEGORIES:A,Generative" in text
    assert "CATEGORIES:B,Rewriting" in text


def test_overlap_reads_prefixed_cells():
    clash = FREE.replace("| 17:30-19:00 |", "| 12:30-19:00 |")
    pairs = find_overlaps(parse_text(clash).events)
    assert pairs


# -- starter templates ---------------------------------------------------------
def test_the_standard_template_is_unchanged():
    assert template_string(3) == template_string(3, "standard")


@pytest.mark.parametrize("style, order, first", [
    ("morning", ["Generative", "Rewriting", "Supporting"], "05:30"),
    ("evening", ["Supporting", "Rewriting", "Generative"], "12:15"),
    ("split", ["Generative", "Supporting", "Rewriting"], "06:00"),
])
def test_starter_days_have_three_blocks(style, order, first):
    text = template_string(2, style)
    parsed = parse_text(text.replace("|  |", "| A |", 1))
    blocks = [line for line in text.splitlines()
              if line.startswith("| ") and line[2:3].isdigit()]
    assert len(blocks) == 3
    assert blocks[0].startswith(f"| {first}-")
    headers = [line[2:].split(":")[0] for line in text.splitlines()
               if line.rstrip(" |").endswith(":") and line[2:3].isupper()
               and line[3:4].islower()]
    assert headers == order
    assert parsed.legend[:2] == [("A", ""), ("B", "")]


def test_an_unknown_style_is_refused():
    with pytest.raises(ValueError, match="style"):
        template_string(2, "noon")


def test_the_cli_takes_a_style(capsys):
    from writing_schedule.cli import main
    assert main(["template", "1", "--style", "evening"]) in (0, None)
    assert "21:00-23:30" in capsys.readouterr().out


# -- the code as written on the sheets -----------------------------------------
def test_an_event_keeps_its_activity_letter():
    parsed = parse_text(FREE)
    labels = {(e.offset, e.start): e.label for e in parsed.events}
    assert labels[(0, "21:00")] == "gA"
    assert labels[(0, "17:30")] == "eB"
    assert labels[(1, "12:15")] == "E"          # bare, default from the legend
    assert labels[(2, "21:00")] == "GA"         # lowercase without a capital


def test_the_latex_sheet_prints_the_lowercase_letter():
    from writing_schedule.sheet_latex import _spans
    spans = _spans(parse_text(FREE).events, 4)
    labels = [label.split("\\quad")[0] for _sg, _eg, label in spans]
    assert "gA" in labels and "eB" in labels and "sE" in labels
    assert "GA" in labels and "E" in labels


def test_the_week_org_export_prints_the_lowercase_letter():
    import datetime as dt
    from writing_schedule.sheet_org import build_week_org
    text = build_week_org(parse_text(FREE), dt.date(2026, 1, 19))
    assert "| gA | DNPH1 docking :safe: |" in text
    assert "| sE | email |" in text


def test_the_pdf_draws_the_lowercase_letter(tmp_path, monkeypatch):
    import datetime as dt
    from reportlab.pdfgen import canvas
    drawn = []
    original = canvas.Canvas.drawString
    monkeypatch.setattr(canvas.Canvas, "drawString",
                        lambda self, x, y, text, *a, **k:
                        (drawn.append(text), original(self, x, y, text, *a, **k))[1])
    from writing_schedule.sheet import render_week_pdf
    render_week_pdf(parse_text(FREE), dt.date(2026, 1, 19), str(tmp_path / "w.pdf"))
    assert any(t.startswith("gA ") for t in drawn)
    assert any(t.startswith("sE ") for t in drawn)
    assert not any(t.startswith("GQ") for t in drawn)


# -- digit codes ---------------------------------------------------------------

DIGIT_TABLE = """\
| Time        | M  | Tu |
|-------------+----+----|
| 5:00-06:30  | g3 | A  |
| 06:45-08:00 | 3  | e0 |
|-------------+----+----|
| A: 1006AIrxOpt :safe: |  |  |
| 3: 0374qflip @editing  |  |  |
| 0: 2026words           |  |  |
"""


def test_single_digits_are_codes_in_cells_and_legend():
    from writing_schedule.parser import parse_text, split_cell
    assert split_cell("g3") == ("g", "3")
    assert split_cell("7") == (None, "7")
    parsed = parse_text(DIGIT_TABLE)
    assert [code for code, _d in parsed.legend] == ["A", "3", "0"]
    assert parsed.letters == ["0", "3", "A"]
    by_code = {(e.letter, e.start): e.section for e in parsed.events}
    assert by_code[("3", "05:00")] == "Generative"     # the cell letter wins
    assert by_code[("3", "06:45")] == "Rewriting"      # the legend default
    assert by_code[("0", "06:45")] == "Rewriting"


def test_a_time_with_a_one_digit_hour_is_not_a_legend_row():
    from writing_schedule.parser import parse_text
    parsed = parse_text(DIGIT_TABLE)
    assert "5" not in [code for code, _d in parsed.legend]
    assert len(parsed.events) == 4
