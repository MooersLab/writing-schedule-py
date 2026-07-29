"""Time-block sheet tests.

Byte comparison across rendering engines is not realistic, so per the spec we
compare structure: the page count of the produced PDF, and the block-box
geometry computed from the time ranges (drawn at exact positions on the
canvas, not snapped to the five-row grid).
"""

from __future__ import annotations

import warnings

import pytest

from writing_schedule.cli import main
from writing_schedule.parser import parse_text
from writing_schedule.sheet import block_box, render_day_pdf, render_week_pdf
from writing_schedule.sheet_common import block_hours, iter_days
from writing_schedule.week import day_of_week, week_monday

MON = week_monday("2026-01-19")


def _page_count(path: str) -> int:
    import pypdf
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return len(pypdf.PdfReader(path).pages)


def test_week_pdf_has_two_pages_per_day(projects_and_tasks_text, tmp_path):
    parsed = parse_text(projects_and_tasks_text)
    n_days = len({off for _, off in parsed.columns})
    assert n_days == 6
    pdf = str(tmp_path / "week.pdf")
    render_week_pdf(parsed, MON, pdf)
    assert _page_count(pdf) == 2 * n_days


def test_day_pdf_has_two_pages(projects_and_tasks_text, tmp_path):
    parsed = parse_text(projects_and_tasks_text)
    pdf = str(tmp_path / "day.pdf")
    render_day_pdf(parsed, MON, day_of_week(MON, 0), pdf)
    assert _page_count(pdf) == 2


def test_day_pdf_for_absent_day_is_blank_two_pages(projects_and_tasks_text, tmp_path):
    # Sunday has no column in the table, yet a blank two-page sheet is drawn.
    parsed = parse_text(projects_and_tasks_text)
    sunday = day_of_week(MON, 6)
    assert 6 not in {off for _, off in parsed.columns}
    pdf = str(tmp_path / "sun.pdf")
    render_day_pdf(parsed, MON, sunday, pdf)
    assert _page_count(pdf) == 2


def test_iter_days_only_returns_single_day(projects_and_tasks_text):
    parsed = parse_text(projects_and_tasks_text)
    tue = day_of_week(MON, 1)
    days = iter_days(parsed, MON, only=tue)
    assert len(days) == 1
    d, date_str, events = days[0]
    assert d == tue
    assert date_str == "2026-01-20 (Tuesday)"
    assert all(e.offset == 1 for e in events)


def test_sheets_cli_day_writes_single_day(tmp_path):
    parsed_src = tmp_path / "wk.org"
    parsed_src.write_text(
        "| Time <l> | M | Tu |\n|-\n| 04:00-05:30 | A | B |\n|-\n| A: docking |  |  |\n"
    )
    out = tmp_path / "out"
    rc = main(["sheets", str(parsed_src), "--day", "2026-01-20",
               "--dir", str(out), "--format", "both"])
    assert rc == 0
    assert (out / "sheet-2026-01-20.pdf").exists()
    assert (out / "sheet-2026-01-20.org").exists()
    # No week-scoped files were produced.
    assert not list(out.glob("sheets-week-*"))


def test_sheets_cli_requires_week_or_day(tmp_path, capsys):
    src = tmp_path / "wk.org"
    src.write_text("| Time <l> | M |\n|-\n| 04:00-05:30 | A |\n")
    rc = main(["sheets", str(src), "--dir", str(tmp_path / "o")])
    assert rc == 2
    assert "--week" in capsys.readouterr().err


def _mini_table(tmp_path):
    src = tmp_path / "wk.org"
    src.write_text(
        "| Time <l> | M | Tu |\n|-\n| 04:00-05:30 | A | B |\n|-\n| A: docking |  |  |\n"
    )
    return src


def test_generate_cli_day_writes_day_files(tmp_path):
    out = tmp_path / "o"
    rc = main(["generate", str(_mini_table(tmp_path)),
               "--day", "2026-01-20", "--dir", str(out)])
    assert rc == 0
    assert (out / "day-2026-01-20.org").exists()
    assert (out / "day-2026-01-20.ics").exists()
    # No weekly archive file was produced.
    assert not list(out.glob("writing-*"))


def test_export_cli_day_writes_day_ics_only(tmp_path):
    out = tmp_path / "o"
    rc = main(["export", str(_mini_table(tmp_path)),
               "--day", "2026-01-20", "--dir", str(out)])
    assert rc == 0
    assert (out / "day-2026-01-20.ics").exists()
    assert not list(out.glob("*.org"))


def test_generate_cli_requires_week_or_day(tmp_path, capsys):
    rc = main(["generate", str(_mini_table(tmp_path)), "--dir", str(tmp_path / "o")])
    assert rc == 2
    assert "--week" in capsys.readouterr().err


def test_block_box_height_is_proportional_to_time():
    # page one hours 4..13, grid 600 pt tall -> 60 pt per hour.
    a = block_box("04:00", "05:30", 4, 13, grid_top=700.0, grid_bottom=100.0)
    assert a["y_top"] == pytest.approx(700.0)
    assert a["y_top"] - a["y_bottom"] == pytest.approx(90.0)   # 1.5 h * 60
    b = block_box("04:00", "07:00", 4, 13, grid_top=700.0, grid_bottom=100.0)
    assert b["y_top"] - b["y_bottom"] == pytest.approx(180.0)  # 3 h * 60


def test_block_box_off_page_is_none():
    # An evening block does not appear on the morning page.
    assert block_box("20:30", "22:00", 4, 13, 700.0, 100.0) is None


def test_block_box_open_edges_across_page_break():
    # A block crossing the page boundary is open at the edge it runs past.
    top_page = block_box("13:00", "15:00", 4, 13, 700.0, 100.0)
    assert top_page["open_bottom"] is True
    assert top_page["open_top"] is False
    bottom_page = block_box("13:00", "15:00", 14, 23, 700.0, 100.0)
    assert bottom_page["open_top"] is True
    assert bottom_page["open_bottom"] is False


def test_overnight_block_extends_to_midnight():
    assert block_hours("22:00", "06:00") == (22.0, 24.0)
    assert block_hours("04:00", "05:30") == (4.0, 5.5)
