# Command-line reference

The console command is `writing-schedule`. It has six subcommands, and the set
mirrors the shell front end of the elisp package. Every subcommand prints its
own help with `writing-schedule SUBCOMMAND --help`. Run the tool from the root
of the writing-schedule directory, because the example tables and the default
paths are resolved relative to it.

```
writing-schedule generate  TABLE (--week DATE | --day DATE|today) [--dir OUT] [--no-ics] [--no-todo] [--tz ZONE] [--strict]
writing-schedule export    TABLE (--week DATE | --day DATE|today) [--dir OUT] [--no-todo] [--tz ZONE] [--strict]
writing-schedule sheets    TABLE (--week DATE | --day DATE|today) [--dir OUT] [--engine reportlab|latex] [--format pdf|org|both] [--per-day] [--strict]
writing-schedule check     TABLE
writing-schedule template  N [--out FILE]
writing-schedule weeks     [--dir OUT]
```

`--week` accepts any date inside the target week, written as `YYYY-MM-DD`,
because the week snaps to the Monday on or before that date. The `generate`,
`export`, and `sheets` commands also accept `--day`, which names a single day
as `YYYY-MM-DD` or the word `today`. On `generate` and `export` it writes
`day-<ISO>.org` and `day-<ISO>.ics`; on `sheets` it prints only that day's
sheet. Give either `--week` or `--day`.

## Overlapping time blocks

The table places generative, editing, and support activities in separate row
groups, so the same day can carry a block in one group and a clashing block in
another. Each block is a half-open minute interval on its own day, and two
blocks on that day clash when their intervals overlap. Touching blocks, for
example 04:00-05:30 then 05:30-07:00, do not clash. A block that crosses
midnight is compared only against other blocks on its own day.

The `generate`, `export`, and `sheets` commands warn and still write when they
find a clash, because the command line cannot prompt. Pass `--strict` to those
commands to turn the warning into an error that writes nothing and exits 3. The
printed sheet marks each clashing block with an asterisk and a footnote.

## generate

Parse a table and write the dated schedule `.org` file, and, unless you opt
out, the `.ics` calendar beside it.

| Option | Meaning |
|--------|---------|
| `--week DATE` | Any day in the target week. Give this or `--day`. |
| `--day DATE\|today` | A single day, as `YYYY-MM-DD` or the word `today`. Writes `day-<ISO>.org` (and `day-<ISO>.ics`) holding that day's events alone. The `day-` prefix keeps these out of the weekly archive, and the day sets its own week, so `--week` is not needed with it. |
| `--dir OUT` | Output directory. Defaults to the current directory. |
| `--no-ics` | Write only the schedule `.org`, and skip the calendar. |
| `--no-todo` | Omit the `TODO` keyword from each event headline. |
| `--tz ZONE` | The IANA time zone for the calendar, for example `America/Chicago`. Pass an empty string for floating times. |
| `--strict` | Treat overlapping time blocks as an error. Report the clashes and write nothing, exiting 3. |

```
writing-schedule generate examples/my-week.org --week 2026-01-19 --dir out
writing-schedule generate examples/my-week.org --day 2026-01-21 --dir out
writing-schedule generate examples/my-week.org --day today --dir out
```

## export

Write only the `.ics` calendar for a table and a week, or one day. This is
`generate` without the schedule file.

| Option | Meaning |
|--------|---------|
| `--week DATE` | Any day in the target week. Give this or `--day`. |
| `--day DATE\|today` | A single day, as `YYYY-MM-DD` or the word `today`. Writes `day-<ISO>.ics`. |
| `--dir OUT` | Output directory. Defaults to the current directory. |
| `--no-todo` | Omit the `TODO` keyword. |
| `--tz ZONE` | The IANA time zone for the calendar. Pass an empty string for floating times. |
| `--strict` | Treat overlapping time blocks as an error. Report the clashes and write nothing, exiting 3. |

```
writing-schedule export examples/my-week.org --week 2026-01-19 --dir out
writing-schedule export examples/my-week.org --day today --dir out
```

## sheets

Draw the printable time-block sheet, an editable per-day org file, or both.

| Option | Meaning |
|--------|---------|
| `--week DATE` | Any day in the target week. Give this or `--day`. |
| `--day DATE\|today` | A single day, as `YYYY-MM-DD` or the word `today`. Prints only that day's sheet, named `sheet-<ISO>.pdf` (and `sheet-<ISO>.org`). The day sets its own week, so `--week` is not needed with it. |
| `--dir OUT` | Output directory. Defaults to the current directory. |
| `--engine reportlab\|latex` | The PDF engine. `reportlab` is the default and needs no TeX. `latex` emits a `.tex` file for those who have a TeX distribution. |
| `--format pdf\|org\|both` | Which sheet outputs to write. Defaults to `pdf`. |
| `--per-day` | With the ReportLab engine, write one PDF per day rather than one file for the week. Ignored when `--day` names a single day. |
| `--strict` | Treat overlapping time blocks as an error. Report the clashes and write nothing, exiting 3. Without it the sheet is written with the clashes marked. |

Give either `--week` for the whole week or `--day` for one day. A day the
table has no column for prints as a blank sheet, which is useful when today is
not a planned day.

```
writing-schedule sheets examples/my-week.org --week 2026-01-19 --dir out --format both
writing-schedule sheets examples/my-week.org --week 2026-01-19 --dir out --engine latex
writing-schedule sheets examples/my-week.org --day 2026-01-21 --dir out --format both
writing-schedule sheets examples/my-week.org --day today --dir out
```

## check

Report overlapping time blocks in a table and exit 3 when any are found, so it
gates a pre-commit hook or a continuous integration step. It reads only the
table, so it needs neither `--week` nor `--day`. A clean table prints a short
confirmation and exits 0.

```
writing-schedule check examples/my-week.org
```

## template

Print or write a blank weekly table for `N` projects, from 1 to 26. The
scaffold uses single-letter codes that you then rename or replace.

| Option | Meaning |
|--------|---------|
| `--out FILE` | Write the template to this file. Without it, the template prints to standard output. |

```
writing-schedule template 5 --out my-week.org
```

## weeks

List the archived weekly schedule files in a directory, newest first. Only
`writing-YYYY-MM-DD.org` names are listed, so calendar exports and unrelated
org files are ignored.

```
writing-schedule weeks --dir out
```
