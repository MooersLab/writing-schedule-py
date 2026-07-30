"""Tests for same-day time-block overlap detection."""

from writing_schedule.model import Event
from writing_schedule.overlap import (
    conflicting_identities,
    event_identity,
    find_overlaps,
    overlap_lines,
)


def ev(offset, start, end, letter, section="Writing"):
    return Event(section=section, offset=offset, start=start, end=end, letter=letter)


def test_find_overlaps__same_day_clash():
    """writing-schedule/overlap/same-day-clash"""
    events = [ev(2, "09:00", "10:30", "B", "Editing"),
              ev(2, "10:00", "11:00", "C", "Support")]
    conflicts = find_overlaps(events)
    assert len(conflicts) == 1
    assert conflicts[0].offset == 2
    assert conflicts[0].first.letter == "B"
    assert conflicts[0].second.letter == "C"


def test_find_overlaps__touching_blocks_do_not_clash():
    """writing-schedule/overlap/touching-blocks-clean"""
    events = [ev(0, "04:00", "05:30", "A"),
              ev(0, "05:30", "07:00", "B")]
    assert find_overlaps(events) == []


def test_find_overlaps__identical_blocks_clash():
    """writing-schedule/overlap/identical-blocks-clash"""
    events = [ev(0, "09:00", "10:00", "A", "Generative"),
              ev(0, "09:00", "10:00", "B", "Support")]
    conflicts = find_overlaps(events)
    assert len(conflicts) == 1


def test_find_overlaps__three_blocks_yield_expected_pairs():
    """writing-schedule/overlap/three-blocks-pairs"""
    events = [ev(2, "09:00", "11:00", "A"),
              ev(2, "09:30", "09:45", "B"),
              ev(2, "10:00", "12:00", "C")]
    conflicts = find_overlaps(events)
    pairs = {(c.first.letter, c.second.letter) for c in conflicts}
    assert pairs == {("A", "B"), ("A", "C")}


def test_find_overlaps__different_days_do_not_clash():
    """writing-schedule/overlap/different-days-clean"""
    events = [ev(0, "09:00", "10:30", "A"),
              ev(1, "09:00", "10:30", "B")]
    assert find_overlaps(events) == []


def test_find_overlaps__overnight_block_same_day():
    """writing-schedule/overlap/overnight-same-day"""
    events = [ev(0, "22:00", "01:00", "A"),
              ev(0, "23:00", "23:30", "B")]
    assert len(find_overlaps(events)) == 1


def test_find_overlaps__overnight_tail_does_not_reach_next_day():
    """writing-schedule/overlap/overnight-no-cross-day"""
    events = [ev(0, "22:00", "01:00", "A"),   # Monday, tail into Tuesday
              ev(1, "00:30", "01:00", "B")]   # Tuesday early
    assert find_overlaps(events) == []


def test_find_overlaps__empty():
    """writing-schedule/overlap/empty"""
    assert find_overlaps([]) == []


def test_overlap_lines__formats_weekday_and_blocks():
    """writing-schedule/overlap/lines-format"""
    events = [ev(2, "09:00", "10:30", "B", "Editing"),
              ev(2, "10:00", "11:00", "C", "Support")]
    lines = overlap_lines(find_overlaps(events))
    assert lines == [
        "Wednesday: 09:00-10:30 [B, Editing] overlaps 10:00-11:00 [C, Support]"
    ]


def test_conflicting_identities__includes_both_blocks():
    """writing-schedule/overlap/identities"""
    a = ev(2, "09:00", "10:30", "B", "Editing")
    b = ev(2, "10:00", "11:00", "C", "Support")
    clean = ev(2, "13:00", "14:00", "D", "Writing")
    ids = conflicting_identities([a, b, clean])
    assert event_identity(a) in ids
    assert event_identity(b) in ids
    assert event_identity(clean) not in ids
