"""Read an org table from text into rows of cells.

This is the Python stand-in for elisp ``org-table-to-lisp``.  It finds the
first contiguous run of table lines (those starting, after optional leading
whitespace, with ``|``) and returns a list whose elements are either the
sentinel :data:`HLINE` for a horizontal rule or a list of trimmed cell
strings for a data row.

A horizontal rule is any table line whose first character after the leading
``|`` is ``-`` or ``+``, matching org's ``org-table-hline-p``.
"""

from __future__ import annotations

import re
from typing import List, Union

#: Sentinel marking a horizontal rule row (elisp returns the symbol ``hline``).
HLINE = "__HLINE__"

Row = Union[str, List[str]]

_TABLE_LINE = re.compile(r"^[ \t]*\|")
_HLINE_LINE = re.compile(r"^[ \t]*\|[-+]")


def split_row(line: str) -> List[str]:
    """Split one ``| a | b |`` line into trimmed cells ``["a", "b"]``."""
    s = line.strip()
    # Drop the outer pipes, then split on the interior pipes.
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [cell.strip() for cell in s.split("|")]


def parse_org_table(text: str) -> List[Row]:
    """Return the first org table in ``text`` as a list of rows.

    Each row is either :data:`HLINE` or a list of trimmed cell strings.  Lines
    outside the first table run are ignored, so a table embedded in a larger
    org document parses cleanly.
    """
    rows: List[Row] = []
    in_table = False
    for line in text.splitlines():
        if _TABLE_LINE.match(line):
            in_table = True
            if _HLINE_LINE.match(line):
                rows.append(HLINE)
            else:
                rows.append(split_row(line))
        elif in_table:
            # The first non-table line after the table ends the run.
            break
    return rows
