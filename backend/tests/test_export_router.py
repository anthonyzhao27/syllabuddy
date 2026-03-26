"""Endpoint tests for export router behavior."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestIcsExport:
    def test_success_with_course_code(self):
        payload = {
            "events": [
                {
                    "title": "Homework 1",
                    "due_date": "2025-01-30T23:59:00",
                    "course": "CSC413",
                    "event_type": "assignment",
                    "description": "",
                    "time_specified": False,
                }
            ],
            "filename": "syllabus.ics",
            "timezone": "America/Toronto",
        }

        with patch(
            "app.routers.export.create_ics",
            return_value="BEGIN:VCALENDAR\r\nEND:VCALENDAR",
        ):
            response = client.post("/export/ics", json=payload)

        assert response.status_code == 200
        assert "text/calendar" in response.headers["content-type"]
        assert (
            'filename="Syllabuddy - CSC413.ics"'
            in response.headers["content-disposition"]
        )

    def test_empty_events_returns_400(self):
        response = client.post(
            "/export/ics",
            json={
                "events": [],
                "filename": "syllabus.ics",
                "timezone": "America/Toronto",
            },
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "No events to export"

    def test_missing_course_code_returns_400(self):
        payload = {
            "events": [
                {
                    "title": "Event Without Course",
                    "due_date": "2024-01-15T23:59:00",
                    "course": "",
                    "event_type": "assignment",
                    "description": "",
                    "time_specified": True,
                },
            ],
            "filename": "syllabus.ics",
            "timezone": "UTC",
        }

        response = client.post("/export/ics", json=payload)

        assert response.status_code == 400
        assert response.json()["detail"] == "Course code(s) missing"

    def test_mixed_courses_returns_400(self):
        payload = {
            "events": [
                {
                    "title": "HW1",
                    "due_date": "2024-01-15T23:59:00",
                    "course": "CSC413",
                    "event_type": "assignment",
                    "description": "",
                    "time_specified": True,
                },
                {
                    "title": "HW2",
                    "due_date": "2024-01-20T23:59:00",
                    "course": "CSC420",
                    "event_type": "assignment",
                    "description": "",
                    "time_specified": True,
                },
            ],
            "filename": "syllabus.ics",
            "timezone": "UTC",
        }

        response = client.post("/export/ics", json=payload)

        assert response.status_code == 400
        assert "Mixed courses" in response.json()["detail"]

    def test_uses_course_name_in_calendar_name(self):
        payload = {
            "events": [
                {
                    "title": "HW1",
                    "due_date": "2024-01-15T23:59:00",
                    "course": "CSC413",
                    "event_type": "assignment",
                    "description": "",
                    "time_specified": True,
                },
            ],
            "filename": "syllabus.ics",
            "timezone": "UTC",
        }

        response = client.post("/export/ics", json=payload)

        assert response.status_code == 200
        assert (
            'filename="Syllabuddy - CSC413.ics"'
            in response.headers["content-disposition"]
        )
        assert "X-WR-CALNAME:Syllabuddy - CSC413" in response.text


class TestOutlookExport:
    def test_single_event_returns_ics(self):
        payload = {
            "events": [
                {
                    "title": "HW1",
                    "due_date": "2024-01-15T23:59:00",
                    "course": "CSC413",
                    "event_type": "assignment",
                    "description": "",
                    "time_specified": True,
                },
            ],
            "timezone": "UTC",
        }

        response = client.post("/export/outlook", json=payload)

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/calendar; charset=utf-8"
        assert (
            'filename="Syllabuddy - CSC413.ics"'
            in response.headers["content-disposition"]
        )

    def test_multiple_events_returns_ics(self):
        payload = {
            "events": [
                {
                    "title": "HW1",
                    "due_date": "2024-01-15T23:59:00",
                    "course": "CSC413",
                    "event_type": "assignment",
                    "description": "",
                    "time_specified": True,
                },
                {
                    "title": "HW2",
                    "due_date": "2024-01-20T23:59:00",
                    "course": "CSC413",
                    "event_type": "assignment",
                    "description": "",
                    "time_specified": True,
                },
            ],
            "timezone": "UTC",
        }

        response = client.post("/export/outlook", json=payload)

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/calendar; charset=utf-8"
        assert (
            'filename="Syllabuddy - CSC413.ics"'
            in response.headers["content-disposition"]
        )

    def test_empty_events_returns_400(self):
        response = client.post(
            "/export/outlook", json={"events": [], "timezone": "America/Toronto"}
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "No events to export"

    def test_missing_course_code_returns_400(self):
        payload = {
            "events": [
                {
                    "title": "Event Without Course",
                    "due_date": "2024-01-15T23:59:00",
                    "course": "",
                    "event_type": "assignment",
                    "description": "",
                    "time_specified": True,
                },
            ],
            "timezone": "UTC",
        }

        response = client.post("/export/outlook", json=payload)

        assert response.status_code == 400
        assert response.json()["detail"] == "Course code(s) missing"

    def test_mixed_courses_returns_400(self):
        payload = {
            "events": [
                {
                    "title": "HW1",
                    "due_date": "2024-01-15T23:59:00",
                    "course": "CSC413",
                    "event_type": "assignment",
                    "description": "",
                    "time_specified": True,
                },
                {
                    "title": "HW2",
                    "due_date": "2024-01-20T23:59:00",
                    "course": "CSC420",
                    "event_type": "assignment",
                    "description": "",
                    "time_specified": True,
                },
            ],
            "timezone": "UTC",
        }

        response = client.post("/export/outlook", json=payload)

        assert response.status_code == 400
        assert "Mixed courses" in response.json()["detail"]


class TestGoogleExport:
    def test_requires_access_token(self):
        payload = {
            "events": [
                {
                    "title": "Homework 1",
                    "due_date": "2025-01-30T23:59:00",
                    "course": "CSC413",
                    "event_type": "assignment",
                    "description": "",
                    "time_specified": False,
                }
            ],
            "calendar_id": "primary",
            "timezone": "America/Toronto",
        }

        response = client.post("/export/google", json=payload)
        assert response.status_code == 400
        assert response.json()["detail"] == "Access token required"

    def test_success_returns_calendar_name(self):
        payload = {
            "events": [
                {
                    "title": "Homework 1",
                    "due_date": "2025-01-30T23:59:00",
                    "course": "CSC413",
                    "event_type": "assignment",
                    "description": "",
                    "time_specified": False,
                }
            ],
            "access_token": "fake-token",
            "calendar_id": "primary",
            "timezone": "America/Toronto",
        }

        with patch(
            "app.routers.export.export_to_google_calendar_sync",
            return_value={
                "created_count": 1,
                "created": [
                    {
                        "title": "Homework 1",
                        "id": "evt_1",
                        "link": "https://calendar.google.com",
                    }
                ],
                "errors": [],
                "calendar_name": "Syllabuddy - CSC413",
            },
        ):
            response = client.post("/export/google", json=payload)

        assert response.status_code == 200
        assert response.json()["created_count"] == 1
        assert response.json()["calendar_name"] == "Syllabuddy - CSC413"

    def test_empty_events_returns_400(self):
        payload = {
            "events": [],
            "access_token": "fake-token",
            "timezone": "America/Toronto",
        }

        response = client.post("/export/google", json=payload)
        assert response.status_code == 400
        assert response.json()["detail"] == "No events to export"

    def test_missing_course_code_returns_400(self):
        payload = {
            "events": [
                {
                    "title": "Event Without Course",
                    "due_date": "2024-01-15T23:59:00",
                    "course": "",
                    "event_type": "assignment",
                    "description": "",
                    "time_specified": True,
                },
            ],
            "access_token": "fake-token",
            "timezone": "UTC",
        }

        with patch(
            "app.routers.export.export_to_google_calendar_sync",
            side_effect=__import__(
                "app.services.calendar_utils", fromlist=["MissingCourseCodeError"]
            ).MissingCourseCodeError(),
        ):
            response = client.post("/export/google", json=payload)

        assert response.status_code == 400
        assert response.json()["detail"] == "Course code(s) missing"

    def test_mixed_courses_returns_400(self):
        payload = {
            "events": [
                {
                    "title": "HW1",
                    "due_date": "2024-01-15T23:59:00",
                    "course": "CSC413",
                    "event_type": "assignment",
                    "description": "",
                    "time_specified": True,
                },
                {
                    "title": "HW2",
                    "due_date": "2024-01-20T23:59:00",
                    "course": "CSC420",
                    "event_type": "assignment",
                    "description": "",
                    "time_specified": True,
                },
            ],
            "access_token": "fake-token",
            "timezone": "UTC",
        }

        with patch(
            "app.routers.export.export_to_google_calendar_sync",
            side_effect=__import__(
                "app.services.calendar_utils", fromlist=["MixedCourseError"]
            ).MixedCourseError({"CSC413", "CSC420"}),
        ):
            response = client.post("/export/google", json=payload)

        assert response.status_code == 400
        assert "Mixed courses" in response.json()["detail"]

    def test_api_failure_returns_502(self):
        payload = {
            "events": [
                {
                    "title": "Homework 1",
                    "due_date": "2025-01-30T23:59:00",
                    "course": "CSC413",
                    "event_type": "assignment",
                    "description": "",
                    "time_specified": False,
                }
            ],
            "access_token": "fake-token",
            "calendar_id": "primary",
            "timezone": "America/Toronto",
        }

        with patch(
            "app.routers.export.export_to_google_calendar_sync",
            side_effect=RuntimeError("upstream failed"),
        ):
            response = client.post("/export/google", json=payload)

        assert response.status_code == 502
