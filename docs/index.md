# writing-schedule

`writing-schedule` turns a weekly org-mode block table into three artifacts,
namely a dated schedule `.org` file, an iCalendar `.ics` file, and a printable
time-block PDF. It is a Python port of the Emacs package
`mooerslab/writing-schedule.el`, and it produces the same schedule and the same
calendar from the same table.

You do not need Emacs, and you do not need `writing-schedule.el`, to use this
package. It is a standalone command-line program and Python library whose only
runtime dependency is ReportLab, because the PDF is drawn with ReportLab
rather than with a TeX distribution.

The weekly table is the single planning surface. You write it in any text
editor, you keep it under version control if you wish, and the tool stamps it
with real dates and hands the result to your calendar, your org agenda, and
your printer.

```{toctree}
:maxdepth: 2
:caption: User guide

installation
tutorial
org-format
cli
library
daylight-saving
```

```{toctree}
:maxdepth: 2
:caption: Reference

api
development
```

## A one-minute example

```
pip install writing-schedule
writing-schedule template 5 --out my-week.org   # scaffold a blank table
# edit my-week.org to place your project codes in the day cells
writing-schedule generate my-week.org --week 2026-01-19 --dir out
writing-schedule sheets   my-week.org --week 2026-01-19 --dir out --format both
```

The first command scaffolds a blank table, the `generate` command writes the
dated schedule and the calendar, and the `sheets` command draws the printable
PDF and an editable per-day org file.
