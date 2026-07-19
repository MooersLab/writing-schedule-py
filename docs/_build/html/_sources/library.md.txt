# Using the library

The package exposes a small public API, so you can parse a table and build the
outputs from your own Python without the command line. The functions and
classes below are re-exported from the top-level `writing_schedule` package,
and the full signatures are in the [API reference](api.md).

## Parse a table

```python
from writing_schedule import parse_text

parsed = parse_text(open("examples/my-week.org").read())
print(len(parsed.events), "events")
print(parsed.letters)          # sorted, de-duplicated codes
print(parsed.legend_lookup("A"))
```

`parse_text` returns a {class}`~writing_schedule.model.ParsedTable`, which holds
the events, the legend, the codes, and the day columns. The parser knows
nothing about output formats, so the same structure feeds every writer.

## Write the schedule and the calendar

```python
from writing_schedule import parse_text, generate_schedule, build_ics

parsed = parse_text(open("examples/my-week.org").read())
monday, title, body = generate_schedule(parsed, "2026-01-19")

with open("writing-2026-01-19.org", "w") as fh:
    fh.write(body)

with open("writing-2026-01-19.ics", "w", newline="") as fh:
    fh.write(build_ics(parsed, monday, title))
```

`generate_schedule` snaps the date to the Monday and returns that Monday, the
title, and the full file body, including the Summary section. `build_ics`
writes the calendar directly, with a `TZID` and a `VTIMEZONE`, so the times are
unambiguous across a daylight-saving transition.

## Draw the sheet and the editable week

```python
from writing_schedule import parse_text, render_week_pdf, build_week_org, week_monday

parsed = parse_text(open("examples/my-week.org").read())
monday = week_monday("2026-01-19")

render_week_pdf(parsed, monday, "sheets-week-2026-01-19.pdf")

with open("sheets-week-2026-01-19.org", "w") as fh:
    fh.write(build_week_org(parsed, monday))
```

## Configure behavior

Pass a {class}`~writing_schedule.config.Config` to change the time zone, turn
the `TODO` keyword off, adjust the sheet geometry, or supply a standing
dictionary of code descriptions.

```python
from writing_schedule import Config, parse_text, build_ics, generate_schedule

cfg = Config(
    timezone="America/New_York",
    use_todo=False,
    code_descriptions={"CM": "commute in morning"},
)
parsed = parse_text(open("examples/my-week.org").read())
monday, title, body = generate_schedule(parsed, "2026-01-19", cfg)
ics = build_ics(parsed, monday, title, cfg)
```

## Scaffold a blank table

```python
from writing_schedule import template_string

print(template_string(5))   # a blank table for five projects
```
