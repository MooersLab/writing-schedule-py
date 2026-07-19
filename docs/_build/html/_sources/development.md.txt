# Development

This page covers the test suite, the parity fixtures, and the Makefile. The
package is small and dependency-light, so a working session needs only a
checkout and an editable install.

## Testing and parity

```
pip install -e ".[test]"
pytest
```

The suite has several layers. `tests/test_writing_schedule.py` ports the Emacs
ERT suite to pytest and keeps the same test names, so the two suites read side
by side. `tests/test_parity.py` asserts that the parser finds forty-four events
with the correct codes, offsets, and times in the canonical fixture, which is
the hardest shared contract. `tests/test_ics.py` covers the calendar subset and
daylight saving, and `tests/test_sheet.py` checks the PDF page count and the
block-box geometry, because byte comparison across two rendering engines is not
realistic.

`tests/test_frozen_fixtures.py` is the tuning fork. It diffs the Python schedule
`.org` and week `.org` byte-for-byte against output frozen from the elisp
reference, so the two implementations stay aligned to a fixed reference rather
than to each other. The calendar is checked two ways, namely a byte-for-byte
match against a frozen Python golden and a semantic match against the elisp
`ox-icalendar` export that compares the set of events by local start, local
end, summary, and categories. The frozen files and their provenance live in
`tests/fixtures/expected/`.

## The Makefile

The repository ships a `Makefile` that wraps the common tasks. Run `make` with
no target, or `make help`, to list them.

| Target | What it does |
|--------|--------------|
| `make dev` | Install the package in editable mode with the test extras. |
| `make test` | Run the pytest suite. |
| `make coverage` | Run the tests with a line-coverage report. |
| `make lint` | Lint with ruff when it is installed. |
| `make demo` | Generate the schedule, calendar, and sheets from an example table into `out/`. |
| `make build` | Build the sdist and wheel into `dist/`. |
| `make check` | Build, then validate the distributions with twine. |
| `make publish-test` | Upload to TestPyPI. |
| `make publish` | Upload to PyPI. |
| `make reference` | Refresh the frozen elisp fixtures from Emacs. |
| `make clean` | Remove caches, build artifacts, and the demo output. |

The demo reads its inputs from variables, so it can point at any table and
week:

```
make demo TABLE=examples/my-week.org WEEK=2026-03-02 OUT=build/demo
```

The `reference` target needs Emacs and the path to the elisp package, because
it runs the reference implementation to rewrite the files in
`tests/fixtures/expected/`:

```
make reference WS_EL=../writing-schedule.el
```

## Building these docs

The documentation is a Sphinx project under `docs/`. Build it locally with the
documentation requirements installed:

```
pip install -r docs/requirements.txt
sphinx-build -b html docs docs/_build/html
```

Read the Docs builds the same project from `.readthedocs.yaml`, which installs
the package so autodoc can import it, installs `docs/requirements.txt`, and
fails the build on any warning.
