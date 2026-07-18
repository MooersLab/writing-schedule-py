"""Draw the printable time-block sheet with ReportLab (the default engine).

This replaces the TeX dependency with a pure-Python one.  The sheet is a
rectangular grid, so drawing lines and text at absolute coordinates is a
natural fit: each planned block is a box that spans its exact time range,
rather than snapping to the five-row-per-hour grid the LaTeX/tabular model
forces.  The sub-rows survive only as light guide lines, which is the
improvement the format spec recommends for a canvas renderer.

Layout follows the spec's geometry: a code key across the top, a Date row and
two blank rows, hour labels down a narrow left column, planned blocks drawn as
heavy outlined boxes in the first wide (plan) column, and the remaining plan
columns left blank for revisions.  Each day is two pages, split at the same
hour the reference uses; a block reaching a page edge is left open there.
"""

from __future__ import annotations

import datetime as _dt
from typing import List, Optional, Tuple

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm, inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from .config import Config
from .model import Event, ParsedTable
from .sheet_common import block_hours, iter_days, key_pairs, page_split, tidy

_PAGE = letter
_MARGIN = 0.5 * inch
_TIME_W = 1 * cm
_PLAN_W = 4 * cm
_HEADER_ROW_H = 18.0
_KEY_FONT = ("Helvetica", 8)
_KEY_LABEL_FONT = ("Helvetica-Bold", 8)


def block_box(start: str, end: str, page_lo: int, page_hi: int,
              grid_top: float, grid_bottom: float):
    """Return the block's box geometry on a page, or None if it is off-page.

    Pure geometry, factored out so tests can check that a block from t1 to t2
    maps to y positions proportional to its time range.  Returns a dict with
    ``y_top``/``y_bottom`` (points), the clipped ``start``/``end`` (hours), and
    ``open_top``/``open_bottom`` flags for blocks that run past a page edge.
    """
    total = page_hi - page_lo + 1
    hour_h = (grid_top - grid_bottom) / total
    s, e = block_hours(start, end)
    if e <= page_lo or s >= page_hi + 1:
        return None
    open_top = s < page_lo
    open_bottom = e > page_hi + 1
    cs = max(s, float(page_lo))
    ce = min(e, float(page_hi + 1))
    return {
        "y_top": grid_top - (cs - page_lo) * hour_h,
        "y_bottom": grid_top - (ce - page_lo) * hour_h,
        "start": cs,
        "end": ce,
        "open_top": open_top,
        "open_bottom": open_bottom,
    }


def _wrap(text: str, font: str, size: float, max_width: float,
          first_indent: float = 0.0) -> List[str]:
    """Greedy word wrap; the first line may be shortened by ``first_indent``."""
    words = text.split()
    lines: List[str] = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        avail = max_width - (first_indent if not lines else 0)
        if stringWidth(trial, font, size) <= avail or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def _key_text(pairs: List[Tuple[str, str]]) -> str:
    parts = [f"{ltr} = {desc}" if desc else ltr for ltr, desc in pairs]
    return ", ".join(parts)


def _draw_page(c: canvas.Canvas, date_str: str, key_text: str,
               events: List[Event], page_lo: int, page_hi: int,
               cfg: Config) -> None:
    pw, ph = _PAGE
    ncols = cfg.timeblock_columns
    subrows = cfg.timeblock_subrows
    table_w = _TIME_W + ncols * _PLAN_W
    left = (pw - table_w) / 2.0
    right = left + table_w
    top = ph - _MARGIN

    # --- Key line(s) across the top ---
    kfont, ksize = _KEY_FONT
    label = "Key:  "
    indent = stringWidth(label, _KEY_LABEL_FONT[0], _KEY_LABEL_FONT[1])
    key_lines = _wrap(key_text, kfont, ksize, table_w, first_indent=indent)
    y = top - ksize
    c.setFillColorRGB(0, 0, 0)
    c.setFont(_KEY_LABEL_FONT[0], _KEY_LABEL_FONT[1])
    c.drawString(left, y, "Key:")
    c.setFont(kfont, ksize)
    for i, ln in enumerate(key_lines):
        x = left + indent if i == 0 else left
        c.drawString(x, y, ln)
        y -= ksize + 2
    table_top = y - 4

    # --- Header rows: Date row + two blank rows ---
    grid_top = table_top - 3 * _HEADER_ROW_H
    grid_bottom = _MARGIN
    total_hours = page_hi - page_lo + 1
    hour_h = (grid_top - grid_bottom) / total_hours
    subrow_h = hour_h / subrows

    def y_of(t_hours: float) -> float:
        return grid_top - (t_hours - page_lo) * hour_h

    # Date row text.
    c.setFont("Helvetica", 9)
    c.drawString(left + 4, table_top - 13, f"Date: {date_str}")

    # --- Hour guide grid ---
    # Light sub-row guides across the plan columns.
    c.setLineWidth(0.3)
    c.setStrokeColorRGB(0.78, 0.78, 0.78)
    for h in range(page_lo, page_hi + 1):
        for sr in range(1, subrows):
            gy = y_of(h + sr / subrows)
            c.line(left + _TIME_W, gy, right, gy)

    # Solid hour separators, full width.
    c.setLineWidth(0.6)
    c.setStrokeColorRGB(0, 0, 0)
    for h in range(page_lo, page_hi + 2):
        c.line(left, y_of(h), right, y_of(h))
    # Hour labels in the time column.
    c.setFont("Helvetica", 8)
    for h in range(page_lo, page_hi + 1):
        c.drawString(left + 2, y_of(h) - 9, f"{h}:00")

    # --- Rules under the Date row and under the blank rows ---
    c.setLineWidth(0.6)
    c.line(left, table_top - _HEADER_ROW_H, right, table_top - _HEADER_ROW_H)
    c.line(left, grid_top, right, grid_top)

    # --- Vertical rules ---
    # Time-column divider (solid) below the Date row.
    c.setLineWidth(0.6)
    c.line(left + _TIME_W, table_top - _HEADER_ROW_H, left + _TIME_W, grid_bottom)
    # Dashed dividers between plan columns.
    c.setDash(2, 2)
    for i in range(1, ncols):
        x = left + _TIME_W + i * _PLAN_W
        c.line(x, table_top - _HEADER_ROW_H, x, grid_bottom)
    c.setDash()  # solid again

    # --- Outer border (solid), encloses header + grid ---
    c.setLineWidth(1.0)
    c.rect(left, grid_bottom, table_w, table_top - grid_bottom, stroke=1, fill=0)

    # --- Planned blocks, drawn at exact positions in the first plan column ---
    box_left = left + _TIME_W
    box_right = box_left + _PLAN_W
    for ev in events:
        box = block_box(ev.start, ev.end, page_lo, page_hi, grid_top, grid_bottom)
        if box is None:
            continue  # not on this page
        open_top = box["open_top"]
        open_bottom = box["open_bottom"]
        yt = box["y_top"]
        yb = box["y_bottom"]
        c.setLineWidth(1.3)
        c.setStrokeColorRGB(0, 0, 0)
        c.line(box_left, yt, box_left, yb)      # left heavy rule
        c.line(box_right, yt, box_right, yb)    # right heavy rule
        if not open_top:
            c.line(box_left, yt, box_right, yt)
        if not open_bottom:
            c.line(box_left, yb, box_right, yb)
        if not open_top:
            c.setFont("Helvetica-Bold", 8)
            label = f"{ev.letter}  {tidy(ev.start)}-{tidy(ev.end)}"
            c.drawString(box_left + 3, yt - 10, label)


def _draw_day(c: canvas.Canvas, date_str: str, key_text: str,
              events: List[Event], cfg: Config) -> None:
    lo = cfg.timeblock_start_hour
    hi = cfg.timeblock_end_hour
    mid = page_split(lo, hi)
    _draw_page(c, date_str, key_text, events, lo, mid, cfg)
    c.showPage()
    _draw_page(c, date_str, key_text, events, mid + 1, hi, cfg)
    c.showPage()


def render_week_pdf(parsed: ParsedTable, monday: _dt.date, path: str,
                    config: Optional[Config] = None) -> str:
    """Draw the whole week (two pages per day) into one PDF at ``path``."""
    cfg = config or Config()
    key_text = _key_text(key_pairs(parsed, cfg))
    c = canvas.Canvas(path, pagesize=_PAGE)
    c.setTitle(f"Time-block sheets, week of {monday.isoformat()}")
    for _d, date_str, events in iter_days(parsed, monday):
        _draw_day(c, date_str, key_text, events, cfg)
    c.save()
    return path


def render_day_pdf(parsed: ParsedTable, monday: _dt.date, day_date: _dt.date,
                   path: str, config: Optional[Config] = None) -> str:
    """Draw a single day (two pages) into a PDF at ``path``."""
    cfg = config or Config()
    key_text = _key_text(key_pairs(parsed, cfg))
    date_str = None
    events: List[Event] = []
    for d, ds, evs in iter_days(parsed, monday):
        if d == day_date:
            date_str, events = ds, evs
            break
    if date_str is None:
        date_str = day_date.isoformat()
    c = canvas.Canvas(path, pagesize=_PAGE)
    c.setTitle(f"Time-block sheet, {day_date.isoformat()}")
    _draw_day(c, date_str, key_text, events, cfg)
    c.save()
    return path
