# The org table format

The input is a single org-mode table. The first column is a label column, and
every other column may be a day column. The parser reads the table by testing
the first cell of each row, and horizontal rules are ignored everywhere. Four
kinds of row carry meaning, namely the header row, the legend row, the
time-block row, and the section header row. They are tested in that order, and
the first test that matches wins.

## The header row

The header row is the first row in which a cell after the first names a
weekday. Its first column is a plain label, such as `Time`, and every column
after it that names a day becomes a day column. The accepted day spellings are
listed below. Matching ignores case and surrounding whitespace.

| Offset from Monday | Accepted spellings |
|--------------------|--------------------|
| 0 | m, mo, mon |
| 1 | tu, tue |
| 2 | w, we, wed |
| 3 | th, thu |
| 4 | f, fr, fri |
| 5 | sa, sat |
| 6 | su, sun |

Day columns need not be contiguous, need not be in order, and need not cover
all seven days, so a week of only Monday and Thursday is valid. A lone `T` is
not accepted, because it is ambiguous between Tuesday and Thursday. Longer
spellings such as `monday` are not accepted either.

## The section header row

A section header row is a line whose first cell is a word or a few words with
an optional trailing colon, such as `Generative:`. It groups the blocks
beneath it, and its name becomes the `CATEGORY` property in the schedule file.
An activity letter in a cell or a default activity in the legend overrides it
for that block.
The pattern accepts letters and spaces only, so a name that contains a digit,
such as `Deep Work 1`, is not recognized as a section. Before any section
header appears, the section is `Writing`.

## The time-block row

A time-block row is a row whose first cell holds a time range, such as
`04:00-05:30`, once the day columns have been found. Each non-empty day cell
under the time produces one event. The cell text is upper-cased to become the
event code, unless it starts with an activity letter, which the next sections
describe.

The time reader is forgiving. The following variations all parse to the same
zero-padded `HH:MM` range.

| Written | Read as | Reason |
|---------|---------|--------|
| `4:00-5:30` | 04:00-05:30 | The hour may be one digit. |
| `16: 30-17: 00` | 16:30-17:00 | A space may follow the colon. |
| `09:00 -- 10:00` | 09:00-10:00 | One or more hyphens, with spaces, are allowed. |
| `Block 9:00-10:00` | 09:00-10:00 | The range may be embedded in other text. |

Minutes must be exactly two digits. The parser does not range-check the hour or
the minute, so validate your table if that matters to you.

## The legend row

A legend row maps a code to a description, as in `A: DNPH1 docking`. The code
is one uppercase letter followed by up to three more uppercase letters or
digits, so `A`, `EM`, and `W2` are all valid, and you are not limited to four
projects or to single letters. The description is whatever follows the colon.
When the first cell is only the code and a colon, the description may instead
sit in the second cell, which allows a two-column legend layout.

The test for a legend code is case-sensitive, and this is the single most
important rule in the grammar. It is what separates a code from a section
header, because `A: docking` is a legend row while `Generative:` is a section
header. A reader that lower-cased the label before testing would misread every
section header as a legend row.

## Activity letters in the cells

A day cell may name the activity of its block with one lowercase letter
before the code. `gA` is generative writing on project A, `eA` is editing
on A, and `sEM` is support work on EM. The letter becomes the section of
the event (`Generative`, `Rewriting`, or `Supporting`), so the schedule
file, the calendar file, the clash check, and the sheets treat the block
exactly as if it sat under that section header. The code itself is stored
without the letter.

The letter counts only when it is a lowercase `g`, `e`, or `s` followed by
a capital. A cell typed all in lowercase, such as `ga`, is still read as
the code `GA`, as before.

With activity letters, a table needs no section rows at all, and one time
slot can hold different activities on different days. This suits a writer
who drafts late in the evening.

```
| Time        | M  | Tu | W  |
|-------------+----+----+----|
| 12:15-13:00 | sE | E  | sE |
| 17:30-19:00 | eB | eA |    |
| 21:00-23:30 | gA | gB | gA |
|-------------+----+----+----|
| A: DNPH1 docking   |  |  |  |
| B: DUSP1 radiation |  |  |  |
| E: email @support  |  |  |  |
```

## Default activities in the legend

A legend entry may name the usual activity of its code with a tag such as
`@generative`, `@editing`, or `@support`, as in `E: email @support`. A bare
`E` in any cell then counts as support. The tag is removed from the
description, and a risk tag such as `:safe:` may follow it.

The risk tags are `:safe:` and `:risky:`. The scheduler reads them as part of
the description and gives them no meaning of its own. The companion package writing-habit reads them for its barbell
split of safe and speculative work, and it labels tracked time on a writing
project that is in neither the legend nor the semester lists of the file as
risky prospecting.

The activity of a block comes from the first of these that is present.

1. An activity letter in the cell, such as `eA`.
2. A default activity on the code's legend entry, such as `@support`.
3. The section header above the row.
4. `Writing`, before any section header.

A table without letters or tags parses exactly as before.

## A worked example

```
| Time <l>          | M  | Tu | W  |
|-------------------+----+----+----|
| Generative:       |    |    |    |
| 04:00-05:30       | A  | B  | A  |
| Supporting:       |    |    |    |
| 16: 30-17:00      | EM | EM | EM |
|-------------------+----+----+----|
| A: DNPH1 docking  |    |    |    |
| EM: email         |    |    |    |
```

This table yields six events. Three carry the section `Generative` and three
carry `Supporting`. The codes are `A`, `B`, and `EM`, and the legend describes
`A` and `EM` but not `B`. A code without a legend entry still produces events,
and its headline falls back to the code itself.

## Codes and descriptions

A code is any short uppercase string in a day cell, so use single letters such
as `A`, `B`, and `C` for projects and two-letter codes such as `EM` for email
or `EX` for exercise for recurring tasks. A description for the sheet key and
the schedule headline comes first from the table legend, which is specific to
the week. A standing dictionary of code descriptions, passed through the
library configuration, fills in any code the legend does not describe.
