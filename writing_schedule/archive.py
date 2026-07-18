"""List archived weekly schedule files, newest first.

Ports ``writing-schedule--archived-weeks``.  ISO dates sort lexically, so a
plain descending string sort orders the weeks from most to least recent.
Only ``writing-YYYY-MM-DD.org`` names are matched, so calendar exports and
unrelated org files are ignored.
"""

from __future__ import annotations

import os
import re
from typing import List, Tuple

_WEEK_RE = re.compile(r"^writing-(\d{4}-\d{2}-\d{2})\.org$")


def archived_weeks(directory: str) -> List[Tuple[str, str]]:
    """Return (ISO-date, path) for each archived week, newest first."""
    out: List[Tuple[str, str]] = []
    if os.path.isdir(directory):
        for name in os.listdir(directory):
            m = _WEEK_RE.match(name)
            if m:
                out.append((m.group(1), os.path.join(directory, name)))
    out.sort(key=lambda t: t[0], reverse=True)
    return out
