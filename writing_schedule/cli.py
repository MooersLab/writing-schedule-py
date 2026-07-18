"""Command-line front end.

Subcommands mirror the shell script and the elisp entry points:

  generate   parse a table and write the dated schedule .org (and .ics)
  export     parse a table and write only the .ics
  sheets     draw the printable time-block sheet (ReportLab or LaTeX) and/or org
  template   print or write a blank weekly table for N projects
  weeks      list archived weekly schedule files, newest first
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

from .config import Config
from .ics import build_ics
from .parser import parse_text
from .schedule import generate_schedule, schedule_filename
from .sheet import render_day_pdf, render_week_pdf
from .sheet_latex import render_latex
from .sheet_org import build_week_org
from .template import template_string
from .week import iso_date, week_monday


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _config_from_args(args) -> Config:
    cfg = Config()
    if getattr(args, "no_todo", False):
        cfg.use_todo = False
    if getattr(args, "tz", None) is not None:
        cfg.timezone = args.tz
    return cfg


def _cmd_generate(args) -> int:
    cfg = _config_from_args(args)
    parsed = parse_text(_read(args.table))
    if not parsed.events:
        print("No filled time blocks found in the table", file=sys.stderr)
        return 2
    monday, title, body = generate_schedule(parsed, args.week, cfg)
    os.makedirs(args.dir, exist_ok=True)
    org_path = os.path.join(args.dir, schedule_filename(monday))
    with open(org_path, "w", encoding="utf-8") as fh:
        fh.write(body)
    print(f"Wrote schedule:  {org_path}")
    if not args.no_ics:
        base = os.path.splitext(os.path.basename(org_path))[0]
        ics_path = os.path.join(args.dir, base + ".ics")
        ics = build_ics(parsed, monday, title, cfg, calname=base)
        with open(ics_path, "w", encoding="utf-8", newline="") as fh:
            fh.write(ics)
        print(f"Wrote iCalendar: {ics_path}")
    return 0


def _cmd_export(args) -> int:
    cfg = _config_from_args(args)
    parsed = parse_text(_read(args.table))
    if not parsed.events:
        print("No filled time blocks found in the table", file=sys.stderr)
        return 2
    monday = week_monday(args.week)
    _, title, _ = generate_schedule(parsed, args.week, cfg)
    base = os.path.splitext(schedule_filename(monday))[0]
    os.makedirs(args.dir, exist_ok=True)
    ics_path = os.path.join(args.dir, base + ".ics")
    ics = build_ics(parsed, monday, title, cfg, calname=base)
    with open(ics_path, "w", encoding="utf-8", newline="") as fh:
        fh.write(ics)
    print(f"Wrote iCalendar: {ics_path}")
    return 0


def _cmd_sheets(args) -> int:
    cfg = _config_from_args(args)
    parsed = parse_text(_read(args.table))
    monday = week_monday(args.week)
    stamp = iso_date(monday)
    os.makedirs(args.dir, exist_ok=True)
    written: List[str] = []

    if args.format in ("pdf", "both"):
        if args.engine == "latex":
            tex_path = os.path.join(args.dir, f"sheets-week-{stamp}.tex")
            with open(tex_path, "w", encoding="utf-8") as fh:
                fh.write(render_latex(parsed, monday, cfg))
            written.append(tex_path)
        elif args.per_day:
            for d, _ds, _evs in _iter_days(parsed, monday):
                p = os.path.join(args.dir, f"sheet-{iso_date(d)}.pdf")
                render_day_pdf(parsed, monday, d, p, cfg)
                written.append(p)
        else:
            p = os.path.join(args.dir, f"sheets-week-{stamp}.pdf")
            render_week_pdf(parsed, monday, p, cfg)
            written.append(p)

    if args.format in ("org", "both"):
        org_path = os.path.join(args.dir, f"sheets-week-{stamp}.org")
        with open(org_path, "w", encoding="utf-8") as fh:
            fh.write(build_week_org(parsed, monday, cfg))
        written.append(org_path)

    for p in written:
        print(f"Wrote {p}")
    return 0


def _iter_days(parsed, monday):
    from .sheet_common import iter_days
    return iter_days(parsed, monday)


def _cmd_template(args) -> int:
    text = template_string(args.n)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"Wrote template to {args.out}")
    else:
        sys.stdout.write(text)
    return 0


def _cmd_weeks(args) -> int:
    from .archive import archived_weeks
    found = archived_weeks(args.dir)
    if not found:
        print(f"No archived weeks in {args.dir}")
    for _iso, path in found:
        print(os.path.basename(path))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="writing-schedule",
        description="Turn a weekly org-table into a schedule, calendar, and sheets.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    g = sub.add_parser("generate", help="write the dated schedule .org (and .ics)")
    g.add_argument("table", help="path to the org table file")
    g.add_argument("--week", required=True, help="any date (YYYY-MM-DD) in the target week")
    g.add_argument("--dir", default=".", help="output directory")
    g.add_argument("--no-ics", action="store_true", help="skip the .ics file")
    g.add_argument("--no-todo", action="store_true", help="omit the TODO keyword")
    g.add_argument("--tz", help="IANA time zone (empty string for floating times)")
    g.set_defaults(func=_cmd_generate)

    e = sub.add_parser("export", help="write only the .ics for a table and week")
    e.add_argument("table")
    e.add_argument("--week", required=True, help="any date in the target week")
    e.add_argument("--dir", default=".", help="output directory")
    e.add_argument("--no-todo", action="store_true")
    e.add_argument("--tz", help="IANA time zone")
    e.set_defaults(func=_cmd_export)

    s = sub.add_parser("sheets", help="draw printable time-block sheets")
    s.add_argument("table")
    s.add_argument("--week", required=True, help="any date in the target week")
    s.add_argument("--dir", default=".", help="output directory")
    s.add_argument("--engine", choices=["reportlab", "latex"], default="reportlab")
    s.add_argument("--format", choices=["pdf", "org", "both"], default="pdf")
    s.add_argument("--per-day", action="store_true", help="one PDF per day (reportlab)")
    s.set_defaults(func=_cmd_sheets)

    t = sub.add_parser("template", help="print or write a blank weekly table")
    t.add_argument("n", type=int, help="number of projects (1-26)")
    t.add_argument("--out", help="write to this file instead of stdout")
    t.set_defaults(func=_cmd_template)

    w = sub.add_parser("weeks", help="list archived weekly schedule files")
    w.add_argument("--dir", default=".", help="directory to scan")
    w.set_defaults(func=_cmd_weeks)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
