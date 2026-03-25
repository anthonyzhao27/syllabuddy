"""Tests for ICS generation service."""

from datetime import datetime

from app.models.schemas import EventType, ParsedEvent
from app.services.ics import (
    _build_summary,
    _escape_ics,
    _fold_ics_line,
    _is_all_day,
    create_ics,
)


class TestEscapeIcs:
    def test_escapes_backslash(self):
        assert _escape_ics("test\\path") == "test\\\\path"

    def test_escapes_semicolon(self):
        assert _escape_ics("item;item") == "item\\;item"

    def test_escapes_comma(self):
        assert _escape_ics("one, two") == "one\\, two"

    def test_escapes_newline(self):
        assert _escape_ics("line1\nline2") == "line1\\nline2"

    def test_handles_empty_string(self):
        assert _escape_ics("") == ""


class TestIsAllDay:
    def test_inferred_time_is_all_day(self):
        event = ParsedEvent(
            title="Homework 1",
            due_date=datetime(2025, 1, 30, 23, 59),
            time_specified=False,
        )
        assert _is_all_day(event) is True

    def test_explicit_time_not_all_day(self):
        event = ParsedEvent(
            title="Midterm",
            due_date=datetime(2025, 1, 30, 14, 0),
            time_specified=True,
        )
        assert _is_all_day(event) is False

    def test_explicit_2359_not_all_day(self):
        event = ParsedEvent(
            title="Real 11:59 PM Deadline",
            due_date=datetime(2025, 1, 30, 23, 59),
            time_specified=True,
        )
        assert _is_all_day(event) is False


class TestFoldIcsLine:
    def test_short_line_unchanged(self):
        assert _fold_ics_line("SUMMARY:Quiz 1") == ["SUMMARY:Quiz 1"]

    def test_long_line_folds_with_continuation_space(self):
        line = "DESCRIPTION:" + ("A" * 120)
        folded = _fold_ics_line(line)

        assert len(folded) > 1
        assert all(part for part in folded)
        assert all(part.startswith(" ") for part in folded[1:])


class TestBuildSummary:
    def test_with_course(self):
        event = ParsedEvent(
            title="Homework 1",
            due_date=datetime(2025, 1, 30, 23, 59),
            course="CS 101",
        )
        assert _build_summary(event) == "[CS 101] Homework 1"

    def test_without_course(self):
        event = ParsedEvent(
            title="Project Due",
            due_date=datetime(2025, 1, 30, 23, 59),
        )
        assert _build_summary(event) == "Project Due"


class TestCreateIcs:
    def test_generates_valid_structure(self):
        events = [
            ParsedEvent(
                title="Test Event",
                due_date=datetime(2025, 1, 30, 23, 59),
            )
        ]
        ics = create_ics(events, "America/Toronto")

        assert "BEGIN:VCALENDAR" in ics
        assert "VERSION:2.0" in ics
        assert "BEGIN:VEVENT" in ics
        assert "END:VEVENT" in ics
        assert "END:VCALENDAR" in ics

    def test_all_day_event_format(self):
        events = [
            ParsedEvent(
                title="All Day",
                due_date=datetime(2025, 1, 30, 23, 59),
                time_specified=False,
            )
        ]
        ics = create_ics(events, "America/Toronto")

        assert "DTSTART;VALUE=DATE:20250130" in ics
        assert "DTEND;VALUE=DATE:20250131" in ics

    def test_timed_event_format(self):
        events = [
            ParsedEvent(
                title="Timed Event",
                due_date=datetime(2025, 1, 30, 14, 0),
                event_type=EventType.EXAM,
                time_specified=True,
            )
        ]
        ics = create_ics(events, "UTC")

        assert "DTSTART:20250130T140000Z" in ics
        assert "DTEND:20250130T150000Z" in ics

    def test_includes_category_for_typed_events(self):
        events = [
            ParsedEvent(
                title="Midterm",
                due_date=datetime(2025, 3, 10, 14, 0),
                event_type=EventType.EXAM,
            )
        ]
        ics = create_ics(events, "America/Toronto")

        assert "CATEGORIES:EXAM" in ics

    def test_default_type_produces_other_category(self):
        events = [
            ParsedEvent(
                title="Something",
                due_date=datetime(2025, 1, 30, 14, 0),
            )
        ]
        ics = create_ics(events, "UTC")

        assert "CATEGORIES:OTHER" in ics

    def test_empty_events_list(self):
        ics = create_ics([], "America/Toronto")

        assert "BEGIN:VCALENDAR" in ics
        assert "END:VCALENDAR" in ics
        assert "BEGIN:VEVENT" not in ics

    def test_crlf_line_endings(self):
        events = [
            ParsedEvent(
                title="Test",
                due_date=datetime(2025, 1, 30, 23, 59),
            )
        ]
        ics = create_ics(events, "America/Toronto")

        assert "\r\n" in ics

    def test_multiple_events(self):
        events = [
            ParsedEvent(title="Event 1", due_date=datetime(2025, 1, 30, 23, 59)),
            ParsedEvent(title="Event 2", due_date=datetime(2025, 2, 15, 14, 0)),
            ParsedEvent(title="Event 3", due_date=datetime(2025, 3, 20, 10, 30)),
        ]
        ics = create_ics(events, "America/Toronto")

        assert ics.count("BEGIN:VEVENT") == 3
        assert ics.count("END:VEVENT") == 3
