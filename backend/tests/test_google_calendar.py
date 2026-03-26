"""Tests for Google Calendar service."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.models.schemas import ParsedEvent
from app.services.google_calendar import (
    _find_calendar_by_name,
    _create_calendar,
    _get_or_create_calendar,
    export_to_google_calendar_sync,
)
from app.services.calendar_utils import MissingCourseCodeError, MixedCourseError


class TestFindCalendarByName:
    def test_finds_existing_calendar_on_first_page(self):
        mock_service = MagicMock()
        mock_service.calendarList().list().execute.return_value = {
            "items": [
                {"id": "cal-1", "summary": "Personal"},
                {"id": "cal-2", "summary": "Syllabuddy - CSC413"},
            ],
        }

        result = _find_calendar_by_name(mock_service, "Syllabuddy - CSC413")

        assert result == "cal-2"

    def test_finds_existing_calendar_with_pagination(self):
        mock_service = MagicMock()
        mock_calendar_list = MagicMock()
        mock_service.calendarList.return_value = mock_calendar_list
        mock_list = MagicMock()
        mock_calendar_list.list.return_value = mock_list
        mock_list.execute.side_effect = [
            {
                "items": [{"id": "cal-1", "summary": "Personal"}],
                "nextPageToken": "token123",
            },
            {
                "items": [{"id": "cal-2", "summary": "Syllabuddy - CSC413"}],
            },
        ]

        result = _find_calendar_by_name(mock_service, "Syllabuddy - CSC413")

        assert result == "cal-2"

    def test_returns_none_when_not_found(self):
        mock_service = MagicMock()
        mock_service.calendarList().list().execute.return_value = {
            "items": [{"id": "cal-1", "summary": "Personal"}],
        }

        result = _find_calendar_by_name(mock_service, "Syllabuddy - CSC413")

        assert result is None


class TestCreateCalendar:
    def test_creates_calendar_with_correct_params(self):
        mock_service = MagicMock()
        mock_calendars = MagicMock()
        mock_service.calendars.return_value = mock_calendars
        mock_insert = MagicMock()
        mock_calendars.insert.return_value = mock_insert
        mock_insert.execute.return_value = {"id": "new-cal-id"}

        result = _create_calendar(
            mock_service, "Syllabuddy - CSC413", "CSC413", "America/New_York"
        )

        assert result == "new-cal-id"
        mock_calendars.insert.assert_called_once()
        call_args = mock_calendars.insert.call_args
        body = call_args[1]["body"]
        assert body["summary"] == "Syllabuddy - CSC413"
        assert body["timeZone"] == "America/New_York"
        assert "CSC413" in body["description"]


class TestGetOrCreateCalendar:
    @patch("app.services.google_calendar._find_calendar_by_name")
    @patch("app.services.google_calendar._create_calendar")
    def test_reuses_existing_calendar(self, mock_create, mock_find):
        mock_find.return_value = "existing-cal-id"
        mock_service = MagicMock()

        result = _get_or_create_calendar(
            mock_service, "Syllabuddy - CSC413", "CSC413", "America/New_York"
        )

        assert result == "existing-cal-id"
        mock_find.assert_called_once_with(mock_service, "Syllabuddy - CSC413")
        mock_create.assert_not_called()

    @patch("app.services.google_calendar._find_calendar_by_name")
    @patch("app.services.google_calendar._create_calendar")
    def test_creates_new_when_not_found(self, mock_create, mock_find):
        mock_find.return_value = None
        mock_create.return_value = "new-cal-id"
        mock_service = MagicMock()

        result = _get_or_create_calendar(
            mock_service, "Syllabuddy - CSC413", "CSC413", "America/New_York"
        )

        assert result == "new-cal-id"
        mock_find.assert_called_once()
        mock_create.assert_called_once_with(
            mock_service, "Syllabuddy - CSC413", "CSC413", "America/New_York"
        )


class TestGoogleCalendarExport:
    @patch("app.services.google_calendar.build")
    @patch("app.services.google_calendar._get_or_create_calendar")
    def test_uses_syllabuddy_prefix_in_calendar_name(
        self, mock_get_or_create, mock_build
    ):
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_get_or_create.return_value = "cal-id"
        mock_service.events().insert().execute.return_value = {
            "id": "evt-1",
            "htmlLink": "https://...",
        }

        events = [
            ParsedEvent(
                title="HW1",
                due_date=datetime(2024, 1, 15),
                course="CSC413",
                type="assignment",
            ),
        ]

        result = export_to_google_calendar_sync(events, "token", "America/New_York")

        assert result["calendar_name"] == "Syllabuddy - CSC413"
        mock_get_or_create.assert_called_once()
        call_args = mock_get_or_create.call_args[0]
        assert call_args[1] == "Syllabuddy - CSC413"
        assert call_args[2] == "CSC413"
        assert call_args[3] == "America/New_York"

    def test_raises_error_for_missing_course(self):
        events = [
            ParsedEvent(
                title="HW1",
                due_date=datetime(2024, 1, 15),
                course="",
                type="assignment",
            ),
        ]

        with pytest.raises(MissingCourseCodeError):
            export_to_google_calendar_sync(events, "token")

    def test_raises_error_for_mixed_courses(self):
        events = [
            ParsedEvent(
                title="HW1",
                due_date=datetime(2024, 1, 15),
                course="CSC413",
                type="assignment",
            ),
            ParsedEvent(
                title="HW2",
                due_date=datetime(2024, 1, 20),
                course="CSC420",
                type="assignment",
            ),
        ]

        with pytest.raises(MixedCourseError):
            export_to_google_calendar_sync(events, "token")

    @patch("app.services.google_calendar.build")
    @patch("app.services.google_calendar._get_or_create_calendar")
    def test_returns_created_count_and_calendar_name(
        self, mock_get_or_create, mock_build
    ):
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_get_or_create.return_value = "cal-id"
        mock_service.events().insert().execute.return_value = {
            "id": "evt-1",
            "htmlLink": "https://calendar.google.com/...",
        }

        events = [
            ParsedEvent(
                title="HW1",
                due_date=datetime(2024, 1, 15),
                course="csc413",
                type="assignment",
            ),
            ParsedEvent(
                title="HW2",
                due_date=datetime(2024, 1, 20),
                course="CSC413",
                type="assignment",
            ),
        ]

        result = export_to_google_calendar_sync(events, "token")

        assert result["created_count"] == 2
        assert result["calendar_name"] == "Syllabuddy - CSC413"
        assert len(result["created"]) == 2
        assert len(result["errors"]) == 0
