# writing-schedule (Python)

A Python port of `mooerslab/writing-schedule.el`. It reads the same weekly org-mode
block table and produces the same three outputs, namely the dated schedule
`.org` file, an iCalendar `.ics` file, and a printable time-block PDF. A
person who cannot install Emacs gets the same artifacts from a single
`pip install`, because the PDF is drawn with ReportLab rather than TeX.
The `.org` file can be exported to HTML or other formats with pandoc.

The org table stays the planning surface, because it is plain text that any
editor can handle. The two implementations are two performances of one score:
the format specification in `formatspec.org` is the score, the elisp package
is the reference recording, and a shared fixture directory keeps the Python
variant from drifting into a dialect of its own.

## Installation

```
pip install writing-schedule        # now published to PyPI
pipx install writing-schedule        # isolated console tool
pip install -e .                     # from a checkout, for development
```

The only runtime dependency is ReportLab. The iCalendar writer and the
parser use the standard library alone, including `zoneinfo` for daylight
saving.

## Command line

The subcommands mirror the shell front end of the elisp package.

```
writing-schedule generate  TABLE --week 2026-01-19 [--dir OUT] [--no-ics] [--no-todo] [--tz ZONE]
writing-schedule export    TABLE --week 2026-01-19 [--dir OUT] [--tz ZONE]
writing-schedule sheets    TABLE --week 2026-01-19 [--dir OUT] [--engine reportlab|latex] [--format pdf|org|both] [--per-day]
writing-schedule template  N [--out FILE]
writing-schedule weeks     [--dir OUT]
```

`--week` takes any date inside the target week, because the week snaps to the
Monday on or before that date. Examples:

```
writing-schedule generate projects-and-tasks.org --week 2026-01-19 --dir out
writing-schedule sheets   projects-and-tasks.org --week 2026-01-19 --dir out --format both
writing-schedule sheets   projects-and-tasks.org --week 2026-01-19 --dir out --engine latex
```

## Library

```python
from writing_schedule import parse_text, generate_schedule, build_ics, render_week_pdf

parsed = parse_text(open("projects-and-tasks.org").read())
monday, title, body = generate_schedule(parsed, "2026-01-19")
open("writing-2026-01-19.org", "w").write(body)
open("writing-2026-01-19.ics", "w", newline="").write(build_ics(parsed, monday, title))
render_week_pdf(parsed, monday, "sheets-week-2026-01-19.pdf")
```

## Module layout

| Module          | Responsibility                          | Mirrors                         |
|-----------------|-----------------------------------------|---------------------------------|
| `parser.py`     | Read the org table into events          | `writing-schedule--parse`       |
| `orgtable.py`   | Split org-table text into rows          | `org-table-to-lisp`             |
| `model.py`      | Event, ParsedTable, MapEntry            | the reference plists            |
| `week.py`       | Week arithmetic and date stamping       | `--week-monday`, `--iso-date`   |
| `schedule.py`   | Write the dated schedule org file        | `writing-schedule-generate`     |
| `ics.py`        | Emit RFC 5545 events directly           | the `ox-icalendar` export       |
| `vtimezone.py`  | Build a VTIMEZONE from `zoneinfo`        | (improvement over floating time)|
| `sheet.py`      | Draw the time-block PDF (ReportLab)     | the `--timeblock-*` family      |
| `sheet_latex.py`| Emit the LaTeX sheet (optional engine)  | `--timeblock-document`          |
| `sheet_org.py`  | Write the editable week org file        | `--timeblock-org-document`      |
| `template.py`   | Blank weekly-table scaffold             | `--template-string`             |
| `archive.py`    | List archived weeks, newest first       | `--archived-weeks`              |
| `cli.py`        | Subcommands and options                 | `writing-schedule.sh`           |

The parser is free of any knowledge of output formats. It returns a plain
data structure of events, the legend, the codes, and the day columns, so a
bug in the PDF layout can never corrupt the calendar output.

## The PDF decision

ReportLab is the default, because a person who cannot install Emacs is
unlikely to enjoy installing a multi-gigabyte TeX distribution. Drawing the
grid is a good fit for a canvas, because each planned block is a box placed at
its exact time range rather than snapped to the five-row-per-hour grid the
tabular model forces. The five sub-rows survive only as light guide lines. A
block that reaches a page boundary is left open at that edge, so a block
crossing the page break reads as one block across two pages.

The LaTeX emitter is kept behind `--engine latex` for users who have TeX and
want output that is byte-comparable with the Emacs version.

## Daylight saving

Times are written as local wall-clock values with a `TZID`, and the file
carries a `VTIMEZONE` derived from `zoneinfo`. A 04:00 block therefore stays
at 04:00 in every week, and a calendar client resolves the correct absolute
instant on either side of a transition. The test suite verifies that a 04:00
block resolves to 10:00 UTC in a winter week and 09:00 UTC in a summer week.

## Testing and parity

```
pip install -e ".[test]"
pytest
```

`tests/test_writing_schedule.py` ports the ERT suite to pytest and keeps the
same test names, so the two suites read side by side. `tests/test_parity.py`
asserts that the parser finds forty-four events with the correct codes,
offsets, and times in `tests/fixtures/projects-and-tasks.org`, which is the
hardest shared contract. `tests/test_ics.py` covers the calendar subset and
daylight saving. `tests/test_sheet.py` checks the PDF page count and the
block-box geometry, because byte comparison across two rendering engines is
not realistic.
