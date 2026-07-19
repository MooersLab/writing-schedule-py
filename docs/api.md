# API reference

This page documents the public modules. The everyday names, such as
`parse_text`, `generate_schedule`, `build_ics`, and `render_week_pdf`, are
re-exported from the top-level `writing_schedule` package, and their canonical
definitions are shown below under the module that owns them.

## Parsing

```{eval-rst}
.. automodule:: writing_schedule.orgtable
   :members:

.. automodule:: writing_schedule.parser
   :members:

.. automodule:: writing_schedule.model
   :members:
```

## Dates

```{eval-rst}
.. automodule:: writing_schedule.week
   :members:
```

## Schedule and calendar

```{eval-rst}
.. automodule:: writing_schedule.schedule
   :members:

.. automodule:: writing_schedule.ics
   :members:

.. automodule:: writing_schedule.vtimezone
   :members:
```

## Sheets

```{eval-rst}
.. automodule:: writing_schedule.sheet
   :members:

.. automodule:: writing_schedule.sheet_common
   :members:

.. automodule:: writing_schedule.sheet_latex
   :members:

.. automodule:: writing_schedule.sheet_org
   :members:
```

## Configuration and utilities

```{eval-rst}
.. automodule:: writing_schedule.config
   :members:

.. automodule:: writing_schedule.template
   :members:

.. automodule:: writing_schedule.archive
   :members:
```

## Command line

```{eval-rst}
.. automodule:: writing_schedule.cli
   :members:
```
