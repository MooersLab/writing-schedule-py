# Command-line reference

The console command is `writing-schedule`. It has five subcommands, and the set
mirrors the shell front end of the elisp package. Every subcommand prints its
own help with `writing-schedule SUBCOMMAND --help`.

```
writing-schedule generate  TABLE --week DATE [--dir OUT] [--no-ics] [--no-todo] [--tz ZONE]
writing-schedule export    TABLE --week DATE [--dir OUT] [--no-todo] [--tz ZONE]
writing-schedule sheets    TABLE --week DATE [--dir OUT] [--engine reportlab|latex] [--format pdf|org|both] [--per-day]
writing-schedule template  N [--out FILE]
writing-schedule weeks     [--dir OUT]
```

`--week` accepts any date inside the target week, written as `YYYY-MM-DD`,
because the week snaps to the Monday on or before that date.

## generate

Parse a table and write the dated schedule `.org` file, and, unless you opt
out, the `.ics` calendar beside it.

| Option | Meaning |
|--------|---------|
| `--week DATE` | Any day in the target week. Required. |
| `--dir OUT` | Output directory. Defaults to the current directory. |
| `--no-ics` | Write only the schedule `.org`, and skip the calendar. |
| `--no-todo` | Omit the `TODO` keyword from each event headline. |
| `--tz ZONE` | The IANA time zone for the calendar, for example `America/Chicago`. Pass an empty string for floating times. |

```
writing-schedule generate examples/my-week.org --week 2026-01-19 --dir out
```

## export

Write only the `.ics` calendar for a table and a week. This is `generate`
without the schedule file.

```
writing-schedule export examples/my-week.org --week 2026-01-19 --dir out
```

## sheets

Draw the printable time-block sheet, an editable per-day org file, or both.

| Option | Meaning |
|--------|---------|
| `--week DATE` | Any day in the target week. Required. |
| `--dir OUT` | Output directory. Defaults to the current directory. |
| `--engine reportlab\|latex` | The PDF engine. `reportlab` is the default and needs no TeX. `latex` emits a `.tex` file for those who have a TeX distribution. |
| `--format pdf\|org\|both` | Which sheet outputs to write. Defaults to `pdf`. |
| `--per-day` | With the ReportLab engine, write one PDF per day rather than one file for the week. |

```
writing-schedule sheets examples/my-week.org --week 2026-01-19 --dir out --format both
writing-schedule sheets examples/my-week.org --week 2026-01-19 --dir out --engine latex
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
