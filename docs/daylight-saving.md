# Daylight saving and time zones

Daylight saving is the most likely source of a quiet calendar error, because a
block that looks correct in March can land an hour off in November. This
package avoids that error by writing local wall-clock times with an explicit
time zone.

## How the calendar carries the time

Each event is written as a local wall-clock value with a `TZID` parameter, and
the file carries a `VTIMEZONE` component derived from the standard-library
`zoneinfo` database. A 04:00 block is therefore written literally as `040000`
with a `TZID`, so it stays at 04:00 in every week, and the `VTIMEZONE` supplies
the offset a calendar client needs to compute the correct absolute instant.

The `VTIMEZONE` is not a fixed offset. It carries the daylight and standard
observances for the zone, each with an `RRULE` derived from the transition, for
example the second Sunday of March and the first Sunday of November for the
United States zones. Because the offset comes from the named zone rather than
from a constant, a block keeps its wall-clock time across a transition and the
absolute instant is still correct.

## A verified example

The test suite pins this behavior. A 04:00 block resolves to 10:00 UTC in a
winter week, when the offset is CST, and to 09:00 UTC in a summer week, when the
offset is CDT. In both weeks the local time a calendar shows is 04:00, which is
the property that matters to a person reading the schedule.

## Choosing the zone

The default zone is `America/Chicago`. Set another zone on the command line
with `--tz`, or in the library through the `timezone` field of
{class}`~writing_schedule.config.Config`. Any IANA zone name that `zoneinfo`
knows is accepted.

## Floating times

Passing an empty string as the zone selects floating local times, which is the
behavior of the reference Emacs implementation. A floating time has no `TZID`
and no `VTIMEZONE`, and a calendar client interprets it in the reader's own
zone. This is convenient for a schedule that should read the same everywhere,
but it is ambiguous by definition, so the named-zone default is recommended.
