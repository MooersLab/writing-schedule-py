# writing-schedule (Python)
![Version](https://img.shields.io/static/v1?label=writing-schdule-py&message=0.1.0&color=brightcolor)
[![PyPI version](https://img.shields.io/pypi/v/writing-schedule.svg)](https://pypi.org/project/writing-schedule/)
[![Python versions](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://pypi.org/project/writing-schedule/)
[![Documentation Status](https://readthedocs.org/projects/writing-schedule-py/badge/?version=latest)](https://writing-schedule-py.readthedocs.io/en/latest/?badge=latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Python port of `mooerslab/writing-schedule.el`. It reads the same weekly org-mode
block table and produces the same three outputs, namely the dated schedule
`.org` file, an iCalendar `.ics` file, and a printable time-block PDF. A
person who cannot install Emacs gets the same artifacts from a single
`pip install`, because the PDF is drawn with ReportLab rather than TeX.
The `.org` file can be exported to HTML or other formats with pandoc.

You do not need Emacs, and you do not need `writing-schedule.el`, to use this
package. It is a standalone command-line program and Python library whose only
runtime dependency is ReportLab. The elisp package is the reference
implementation, and it matters only when a developer runs the parity tests
described under Testing and parity.

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

## Tutorial: build a schedule from an org table

The weekly table is the one file you edit. It is an ordinary org-mode table,
so any text editor can produce it, and Emacs is not required. This walkthrough
builds a week from scratch and turns it into the three outputs.

### Step 1, scaffold or copy a table

To start from a blank grid, ask the tool for one and then fill in the cells:

```
writing-schedule template 5 --out my-week.org
```

That writes a blank table for five projects. You can also copy the worked
example below, which is `examples/my-week.org` in the repository.

```
#+TITLE: My Writing Week

| Time <l>    | M  | Tu | W  | Th | F  | Sa |
|-------------+----+----+----+----+----+----|
| Generative: |    |    |    |    |    |    |
| 04:00-05:30 | A  | B  | A  | B  | W  |    |
| 05:45-07:15 | A  | B  | A  | B  | W  | A  |
| Rewriting:  |    |    |    |    |    |    |
| 09:15-10:45 | B  | A  | B  | A  | TT | A  |
| Supporting: |    |    |    |    |    |    |
| 13:15-14:45 | EM | EM | EM | EM | EM |    |
|-------------+----+----+----+----+----+----|
| A:  DNPH1 docking    |  |  |  |  |  |
| B:  DUSP1 radiation  |  |  |  |  |  |
| W:  2026words        |  |  |  |  |  |
| TT: time tracking    |  |  |  |  |  |
| EM: email            |  |  |  |  |  |
```

### Step 2, understand the four kinds of row

The parser reads the table by testing the first cell of each row, and
horizontal rules are ignored. Four kinds of row carry meaning.

The header row is the first row that names weekdays. Its first column is a
plain label, such as `Time`, and every column after it is a day. The accepted
day spellings are m, mo, mon for Monday, then tu or tue, w, we, wed, th or thu,
f, fr, fri, sa or sat, and su or sun. Matching ignores case and surrounding
space. The days may be any subset and in any order, so a week of only Monday
and Thursday is valid. A lone `T` is not accepted, because it is ambiguous
between Tuesday and Thursday.

A section header row is a line whose first cell is a word or a few words with
an optional trailing colon, such as `Generative:`. It groups the blocks
beneath it, and it becomes the `CATEGORY` in the schedule file. Use letters
and spaces only, because a name that contains a digit, such as `Deep Work 1`,
is not recognized as a section.

A time-block row is a row whose first cell holds a time range, such as
`04:00-05:30`. Each day cell beneath the time holds a short code that names
what you work on during that block. The time reader is forgiving, so a
one-digit hour as in `4:00`, a space after the colon as in `16: 30`, extra
spaces, and more than one hyphen are all accepted.

A legend row maps a code to a description, as in `A: DNPH1 docking`. The code
is one uppercase letter followed by up to three more uppercase letters or
digits, so `A`, `EM`, and `W2` are all valid, and you are not limited to four
projects or to single letters. When the first cell is only the code and a
colon, the description may instead sit in the second cell. The code test is
case-sensitive, which is how `A: docking` is read as a legend while
`Generative:` is read as a section header.

### Step 3, generate the outputs

Point the tool at your table and name any day inside the target week, because
the week snaps to the Monday on or before that date.

```
writing-schedule generate examples/my-week.org --week 2026-01-19 --dir out
writing-schedule sheets   examples/my-week.org --week 2026-01-19 --dir out --format both
```

The example table holds twenty-two blocks across five codes and three
sections, and the two commands write these files into `out/`.

| File | What it is |
|------|------------|
| `writing-2026-01-19.org` | The dated schedule, one TODO per block with an active timestamp, and a Summary of hours per code. Add it to your org agenda. |
| `writing-2026-01-19.ics` | The calendar. Import it into Google Calendar, Outlook, or Apple Calendar. |
| `sheets-week-2026-01-19.pdf` | The printable sheet, two pages per day, with the plan in the first column and blank columns to revise as the day changes. |
| `sheets-week-2026-01-19.org` | The same week as an editable per-day org table, in case you prefer to adjust it in org before printing. |

To rework a saved week later, `writing-schedule weeks --dir out` lists the
archived schedule files newest first.

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
writing-schedule generate examples/projects-and-tasks.org --week 2026-01-19 --dir out
writing-schedule sheets   examples/projects-and-tasks.org --week 2026-01-19 --dir out --format both
writing-schedule sheets   examples/projects-and-tasks.org --week 2026-01-19 --dir out --engine latex
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

`tests/test_frozen_fixtures.py` is the tuning fork. It diffs the Python
schedule `.org` and week `.org` byte-for-byte against output frozen from the
elisp reference (GNU Emacs 29.3), so the two implementations stay aligned to a
fixed reference rather than to each other. The calendar is checked two ways: a
byte-for-byte match against a frozen Python golden, and a semantic match
against the elisp `ox-icalendar` export, comparing the set of events by local
start, local end, summary, and categories. The frozen files and their
provenance live in `tests/fixtures/expected/`.

## Using the Makefile

The repository ships a `Makefile` that wraps the common tasks, so you do not
have to remember each command. It is self-documenting, because running `make`
with no target, or `make help`, prints the list.

```
make help
```

The targets fall into three groups, namely working with the package, building
and publishing a release, and refreshing the parity fixtures.

| Target | What it does |
|--------|--------------|
| `make install` | Install the package. |
| `make dev` | Install the package in editable mode with the test extras. |
| `make test` | Run the pytest suite. |
| `make coverage` | Run the tests with a line-coverage report. |
| `make lint` | Lint with ruff when it is installed, and skip with a note when it is not. |
| `make demo` | Generate the schedule, calendar, and sheets from an example table into `out/`. |
| `make build` | Build the sdist and wheel into `dist/`. |
| `make check` | Build, then validate the distributions with twine. |
| `make publish-test` | Upload the built distributions to TestPyPI. |
| `make publish` | Upload the built distributions to PyPI. |
| `make reference` | Refresh the frozen elisp fixtures from Emacs. |
| `make clean` | Remove caches, build artifacts, and the demo output. |

A first session usually runs three targets in order, one to install, one to
test, and one to see real output.

```
make dev
make test
make demo
```

Several targets read their inputs from variables that you can override on the
command line, so the demo can point at any table, week, and output directory:

```
make demo TABLE=examples/my-week.org WEEK=2026-03-02 OUT=build/demo
```

The `reference` target needs Emacs and the path to the elisp package, because
it runs the reference implementation to rewrite the files in
`tests/fixtures/expected/`:

```
make reference WS_EL=../writing-schedule.el
```

The build, check, and coverage targets install `build`, `twine`, and
`pytest-cov` on demand, and only when those tools are missing, so a fresh
checkout still works. If you edit the `Makefile`, keep each recipe line
indented with a tab rather than spaces, because Make requires it.

## Related websites

- MooersLab/writing-schedule
- MooersLab/writing-time-spent-heatmap
- MooersLab/writingLogTemplateInOrg
- MooersLab/writingLogTemplateIn
- MooersLab/whisper-dvr
- MooersLab/programmingLogInOrg

## Sources of funding

- NIH: R01 CA242845.
- NIH: R01 AI088011.
- NIH: P30 CA225520 (PI: R. Mannel).
- NIH: P20 GM103640 and P30 GM145423 (PI: A. West).
