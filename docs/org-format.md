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
The pattern accepts letters and spaces only, so a name that contains a digit,
such as `Deep Work 1`, is not recognized as a section. Before any section
header appears, the section is `Writing`.

## The time-block row

A time-block row is a row whose first cell holds a time range, such as
`04:00-05:30`, once the day columns have been found. Each non-empty day cell
under the time produces one event, and the cell text is upper-cased to become
the event code.

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
