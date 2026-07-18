"""Configuration defaults for the writing-schedule Python port.

Each field mirrors a ``defcustom`` in ``writing-schedule.el``.  Grouping them
in one dataclass keeps the generators pure: they take a :class:`Config` rather
than reading globals, which makes them easy to test.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


# Sections and time blocks used by the blank-template scaffold.  Each element
# is (section-name, [time-range, ...]).  Mirrors ``writing-schedule-default-slots``.
DEFAULT_SLOTS: List[Tuple[str, List[str]]] = [
    ("Generative", ["04:00-05:30", "05:45-07:15", "07:30-09:00"]),
    ("Rewriting", ["09:15-10:45", "11:30-13:00"]),
    ("Supporting", ["13:15-14:45", "15:00-16:30", "16:45-18:15", "20:30-22:00"]),
]

# Default single-letter project codes for a scaffolded template.
PROJECT_LETTERS: List[str] = [chr(c) for c in range(ord("A"), ord("Z") + 1)]


@dataclass
class Config:
    """Runtime configuration for schedule, calendar, and sheet generation."""

    # --- Generated schedule file -----------------------------------------
    #: When True, each generated event headline carries the TODO keyword.
    use_todo: bool = True
    #: The keyword placed before each event when ``use_todo`` is True.
    todo_keyword: str = "TODO"

    # --- iCalendar --------------------------------------------------------
    #: IANA time zone used for the calendar.  An empty string selects the
    #: floating-time behaviour of the reference implementation.
    timezone: str = "America/Chicago"
    #: PRODID advertised by the exporter.
    prodid: str = "-//Blaine Mooers//writing-schedule.py//EN"

    # --- Printable time-block sheet --------------------------------------
    timeblock_start_hour: int = 4
    timeblock_end_hour: int = 23
    #: One planned column plus (columns - 1) revision columns.
    timeblock_columns: int = 4
    #: Writing rows per hour.
    timeblock_subrows: int = 5

    # --- Code descriptions -----------------------------------------------
    #: Standing dictionary of code -> description, merged *under* a table's
    #: own legend (the legend wins).  Used by the sheets, not the schedule.
    code_descriptions: Dict[str, str] = field(default_factory=dict)

    def effective_legend(
        self, legend: List[Tuple[str, str]]
    ) -> List[Tuple[str, str]]:
        """Merge ``code_descriptions`` under ``legend``.

        Entries in ``legend`` take precedence because they are specific to the
        week; the configured descriptions fill in any code the legend omits.
        Mirrors ``writing-schedule--effective-legend``.
        """
        have = {code for code, _ in legend}
        extra = [
            (code, desc)
            for code, desc in self.code_descriptions.items()
            if code not in have
        ]
        return list(legend) + extra
