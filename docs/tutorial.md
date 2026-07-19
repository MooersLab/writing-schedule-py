# Tutorial: build a schedule from an org table

The weekly table is the one file you edit. It is an ordinary org-mode table,
so any text editor can produce it, and Emacs is not required. This walkthrough
builds a week from scratch and turns it into the three outputs. The full
grammar is covered in [The org table format](org-format.md); here you only
need the shape of a table.

## Step 1, scaffold or copy a table

To start from a blank grid, ask the tool for one and then fill in the cells:

```
writing-schedule template 5 --out my-week.org
```

That writes a blank table for five projects. You can also copy the worked
example below, which ships as `examples/my-week.org` in the repository.

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

The first column holds the labels, and every other column is a day. The rows
that start with a section name, such as `Generative:`, group the blocks
beneath them. The rows that start with a time, such as `04:00-05:30`, are the
blocks, and each day cell under a time holds a short code. The rows at the
bottom that start with a code and a colon, such as `A: DNPH1 docking`, name
each code.

## Step 2, generate the outputs

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

## Step 3, live with the week

The printable sheet is meant to be revised. The first column holds the plan,
and the remaining columns are blank, so each time the day changes you write a
new plan in the next column. The rightmost filled column therefore records
what actually happened, which is a record you can transcribe later.

To rework a saved week, list the archive and open the file you want:

```
writing-schedule weeks --dir out
```

The command lists the archived schedule files newest first, because ISO dates
sort in chronological order.

## What each output is for

The dated `.org` file feeds the org agenda, and every block is a `TODO` with an
active timestamp, so the agenda shows your week and the clock tables can total
your hours. The `.ics` file feeds any calendar application through a standard
import. The PDF feeds your printer. The three share one source, so a change to
the table changes all three the next time you run the commands.
