"""A legend kept in columns in a table named This week."""

from writing_schedule import parse_text
from writing_schedule.parser import column_legend

TEXT = """\
| Time | M  | Tu |
|------+----+----|
| 04:00-06:00 | gB | 0 |
| 06:00-07:00 | E  |    |
|------+----+----|

#+NAME: This week
| Code | Project Number | Project Name | Deadline   | Risk tag | Default activity |
|------+----------------+--------------+------------+----------+------------------|
| 0:   | 8721           | Noahlana     | 2026-10-19 | :safe:   |                  |
| B:   | 1006           | AIrxOpt      |            | risky    |                  |
| E:   |                | email        |            |          | support          |
| -    | 1452           | PHFSboXt     |            | :safe:   |                  |
"""


def test_the_columns_read_as_legend_rows():
    assert column_legend(TEXT) == [("0", "8721Noahlana 2026-10-19 :safe:"),
                                   ("B", "1006AIrxOpt :risky:"),
                                   ("E", "email @support")]


def test_parse_text_falls_back_to_the_columns():
    parsed = parse_text(TEXT)
    assert dict(parsed.legend) == {"0": "8721Noahlana 2026-10-19 :safe:",
                                   "B": "1006AIrxOpt :risky:", "E": "email"}
    sections = {(e.letter, e.offset): e.section for e in parsed.events}
    assert sections[("E", 0)] == "Supporting"
    assert sections[("B", 0)] == "Generative"


def test_a_one_cell_legend_still_wins():
    text = TEXT.replace("|------+----+----|\n\n", "|------+----+----|\n| B: other |  |  |\n\n", 1)
    assert dict(parse_text(text).legend) == {"B": "other"}
