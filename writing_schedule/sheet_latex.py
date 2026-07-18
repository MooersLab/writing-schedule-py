"""LaTeX time-block sheet emitter.

A faithful port of the ``writing-schedule--timeblock-*`` LaTeX family, kept as
an optional engine (``--engine latex``) for users who have TeX installed and
want output that is byte-comparable with the Emacs version.  The default
engine is ReportLab (:mod:`writing_schedule.sheet`).
"""

from __future__ import annotations

import datetime as _dt
from typing import List, Optional, Tuple

from .config import Config
from .model import Event, ParsedTable
from .sheet_common import page_split, tidy
from .week import DAY_FULL, day_of_week, iso_date

_LATEX_ESCAPES = [
    ("\\", "\\textbackslash{}"),
    ("&", "\\&"), ("%", "\\%"), ("$", "\\$"), ("#", "\\#"),
    ("_", "\\_"), ("{", "\\{"), ("}", "\\}"),
    ("~", "\\textasciitilde{}"), ("^", "\\textasciicircum{}"),
]


def latex_escape(s: Optional[str]) -> str:
    s = s or ""
    for a, b in _LATEX_ESCAPES:
        s = s.replace(a, b)
    return s


def _colspec(n: int) -> str:
    return "|m{1cm}" + ":m{4cm}" * n + "|"


def _key(pairs: List[Tuple[str, str]]) -> str:
    parts = []
    for ltr, desc in pairs:
        if desc:
            parts.append(f"{ltr} = {latex_escape(desc)}")
        else:
            parts.append(ltr)
    return ",\\quad ".join(parts)


def _spans(events: List[Event], subrows: int) -> List[Tuple[int, int, str]]:
    spans = []
    for ev in events:
        sh, sm = int(ev.start[0:2]), int(ev.start[3:5])
        eh, em = int(ev.end[0:2]), int(ev.end[3:5])
        sg = sh * subrows + min(subrows - 1, (sm * subrows) // 60)
        eg = eh * subrows + min(subrows, (em * subrows) // 60)
        label = f"{ev.letter}\\quad {tidy(ev.start)}-{tidy(ev.end)}"
        if eg <= sg:
            eg = sg + 1
        spans.append((sg, eg, label))
    return spans


def _row(timecol: str, data1: str, ncols: int) -> str:
    cells = [timecol, data1] + [""] * (ncols - 1)
    return " & ".join(cells) + " \\\\"


def _preamble() -> str:
    return (
        "\\documentclass{article}\n"
        "\\usepackage{array}\n"
        "\\usepackage{arydshln}\n"
        "\\usepackage{helvet}\n"
        "\\renewcommand{\\familydefault}{\\sfdefault}\n"
        "\\usepackage[margin=0.5in]{geometry}\n"
        "\\usepackage{booktabs}\n"
        "\\renewcommand{\\arraystretch}{0.8}\n"
        "\\setlength{\\aboverulesep}{0pt}\n"
        "\\setlength{\\belowrulesep}{0pt}\n"
        "\\setlength{\\cmidrulewidth}{1pt}\n"
    )


def _page(date_str, key_str, spans, lo, hi, ncols, subrows) -> str:
    sub = subrows
    lines: List[str] = []
    for h in range(lo, hi + 1):
        for sr in range(sub):
            g = h * sub + sr
            inside = any(s0 <= g < s1 for s0, s1, _ in spans)
            starts = next((sp for sp in spans if sp[0] == g), None)
            ends_after = any(s1 == g + 1 for _, s1, _ in spans)
            timecol = f"{h}:00" if sr == 0 else ""
            label = starts[2] if starts else ""
            if inside:
                cell = (
                    "\\multicolumn{1}{!{\\vrule width 1pt}"
                    "m{4cm}!{\\vrule width 1pt}}{%s}" % label
                )
            else:
                cell = label
            if starts:
                lines.append("\\cmidrule[1pt]{2-2}")
            cells = [timecol, cell] + [""] * (ncols - 1)
            lines.append(" & ".join(cells) + " \\\\")
            if ends_after:
                lines.append("\\cmidrule[1pt]{2-2}")
        lines.append("\\midrule")
    lines = lines[:-1]  # drop the trailing midrule
    return (
        "{\\small\\noindent\\textbf{Key:}\\quad " + key_str + "}\n\n"
        "\\begin{center}\n\\begin{tabular}{" + _colspec(ncols) + "}\n"
        "\\toprule\n"
        "\\multicolumn{" + str(ncols + 1) + "}{|l|}{Date: " + date_str + "} \\\\\n\\midrule\n"
        + _row("", "", ncols) + "\n"
        + _row("", "", ncols) + "\n\\midrule\n"
        + "\n".join(lines) + "\n"
        "\\bottomrule\n\\end{tabular}\n\\end{center}\n"
    )


def _day(date_str, key_str, spans, cfg: Config) -> str:
    lo = cfg.timeblock_start_hour
    hi = cfg.timeblock_end_hour
    ncols = cfg.timeblock_columns
    sub = cfg.timeblock_subrows
    mid = page_split(lo, hi)
    return (
        _page(date_str, key_str, spans, lo, mid, ncols, sub)
        + "\n\\newpage\n"
        + _page(date_str, key_str, spans, mid + 1, hi, ncols, sub)
    )


def render_latex(
    parsed: ParsedTable, monday: _dt.date, config: Optional[Config] = None
) -> str:
    """Return a full LaTeX document with a two-page sheet per day."""
    cfg = config or Config()
    legend = dict(cfg.effective_legend(parsed.legend))
    key_str = _key([(ltr, legend.get(ltr, "")) for ltr in parsed.letters])
    offsets = sorted({off for _, off in parsed.columns})

    day_docs = []
    for off in offsets:
        d = day_of_week(monday, off)
        date_str = f"{iso_date(d)} ({DAY_FULL[d.weekday()]})"
        events = [e for e in parsed.events if e.offset == off]
        day_docs.append(_day(date_str, key_str, _spans(events, cfg.timeblock_subrows), cfg))

    return (
        _preamble()
        + "\n\\begin{document}\n\n"
        + "\n\\clearpage\n".join(day_docs)
        + "\n\\end{document}\n"
    )
