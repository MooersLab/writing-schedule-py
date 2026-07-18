"""writing_schedule: turn a weekly org-table into a schedule, calendar, and sheets.

A Python port of ``writing-schedule.el``.  It reads the same weekly block table
and produces the dated schedule ``.org`` file, an iCalendar ``.ics`` file, and a
printable time-block PDF (drawn with ReportLab, no TeX required), plus an
editable week ``.org`` export.  See the format specification for the shared
contract both implementations satisfy.
"""

from __future__ import annotations

from .config import Config
from .ics import build_ics
from .model import Event, MapEntry, ParsedTable
from .parser import parse_table, parse_text
from .schedule import generate_schedule, schedule_filename
from .sheet import render_day_pdf, render_week_pdf
from .sheet_org import build_week_org
from .template import template_string
from .week import iso_date, week_monday

__version__ = "0.1.0"

__all__ = [
    "Config",
    "Event",
    "MapEntry",
    "ParsedTable",
    "parse_table",
    "parse_text",
    "generate_schedule",
    "schedule_filename",
    "build_ics",
    "build_week_org",
    "render_week_pdf",
    "render_day_pdf",
    "template_string",
    "week_monday",
    "iso_date",
    "__version__",
]
