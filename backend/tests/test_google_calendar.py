"""Tests for Google Calendar export service."""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

from app.models.schemas import EventType, ParsedEvent
from app.services.google_calendar import (
    _build_calendar_event,
    _build_summary,
    export_to_google_calendar_sync,
)


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


class TestBuildCalendarEvent:
    def test_all_day_event(self):
        event = ParsedEvent(
            title="Homework 1",
            due_date=datetime(2025, 1, 30, 23, 59),
            course="CS 101",
            event_type=EventType.ASSIGNMENT,
            time_specified=False,
        )
        result = _build_calendar_event(event, "America/Los_Angeles")

        assert result["summary"] == "[CS 101] Homework 1"
        assert result["start"]["date"] == "2025-01-30"
        assert result["end"]["date"] == "2025-01-31"
        assert "dateTime" not in result["start"]

    def test_timed_event(self):
        event = ParsedEvent(
            title="Midterm Exam",
            due_date=datetime(2025, 3, 10, 14, 0),
            course="CS 101",
            event_type=EventType.EXAM,
        )
        result = _build_calendar_event(event, "America/New_York")

        assert result["summary"] == "[CS 101] Midterm Exam"
        assert "dateTime" in result["start"]
        assert result["start"]["timeZone"] == "America/New_York"
        assert "2025-03-10T14:00:00" in result["start"]["dateTime"]
        assert "2025-03-10T15:00:00" in result["end"]["dateTime"]

    def test_includes_description(self):
        event = ParsedEvent(
            title="Quiz",
            due_date=datetime(2025, 2, 15, 10, 0),
            description="Covers chapters 1-5",
        )
        result = _build_calendar_event(event, "UTC")

        assert result["description"] == "Covers chapters 1-5"


@patch("app.services.google_calendar.build")
def test_export_to_google_calendar_success(mock_build):
    """Test successful export to Google Calendar."""
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.events().insert().execute.return_value = {
        "id": "test-event-id",
        "htmlLink": "https://calendar.google.com/event/test",
    }

    events = [
        ParsedEvent(
            title="Test Event",
            due_date=datetime(2025, 1, 30, 23, 59),
            course="TEST 101",
        )
    ]

    result = export_to_google_calendar_sync(
        events,
        "fake-access-token",
        timezone="America/Toronto",
    )

    assert result["created_count"] == 1
    assert len(result["errors"]) == 0
    assert result["created"][0]["title"] == "Test Event"
    assert result["created"][0]["id"] == "test-event-id"


@patch("app.services.google_calendar.build")
def test_export_to_google_calendar_partial_failure(mock_build):
    """Test export with some events failing."""
    from googleapiclient.errors import HttpError

    mock_service = MagicMock()
    mock_build.return_value = mock_service

    mock_response = Mock()
    mock_response.status = 403
    mock_service.events().insert().execute.side_effect = [
        {"id": "success-id", "htmlLink": "https://example.com"},
        HttpError(resp=mock_response, content=b"Forbidden"),
    ]

    events = [
        ParsedEvent(title="Event 1", due_date=datetime(2025, 1, 30, 23, 59)),
        ParsedEvent(title="Event 2", due_date=datetime(2025, 2, 15, 14, 0)),
    ]

    result = export_to_google_calendar_sync(
        events,
        "fake-token",
        timezone="America/Toronto",
    )

    assert result["created_count"] == 1
    assert len(result["errors"]) == 1
    assert result["errors"][0]["title"] == "Event 2"
