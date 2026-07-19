# Installation

`writing-schedule` runs on Python 3.9 and later. Its only runtime dependency
is ReportLab, which pip installs for you. The parser, the calendar writer, and
the date handling use the standard library alone, including `zoneinfo` for
daylight saving.

## From PyPI

```
pip install writing-schedule
```

To keep the console tool isolated from your other projects, install it with
pipx instead:

```
pipx install writing-schedule
```

## From a checkout

Clone the repository and install it in editable mode, which is the usual
choice for development:

```
git clone https://github.com/MooersLab/writing-schedule
cd writing-schedule
pip install -e ".[test]"
```

The `[test]` extra adds pytest, so you can run the suite described under
[Development](development.md).

## Verifying the installation

```
writing-schedule --help
```

The command prints the five subcommands, namely `generate`, `export`,
`sheets`, `template`, and `weeks`. If the console script is on your path, the
installation is complete.
