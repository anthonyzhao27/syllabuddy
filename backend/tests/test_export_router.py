"""Endpoint tests for export router behavior."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


def _ics_payload() -> dict[str, object]:
    return {
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


def _outlook_payload() -> dict[str, object]:
    return {
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
        "timezone": "America/Toronto",
    }


def _google_payload() -> dict[str, object]:
    return {
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


@pytest.mark.parametrize(
    ("path", "payload"),
    [
        ("/export/ics", _ics_payload()),
        ("/export/outlook", _outlook_payload()),
        ("/export/google", _google_payload()),
    ],
)
def test_export_requires_auth(
    api_client: TestClient,
    path: str,
    payload: dict[str, object],
) -> None:
    response = api_client.post(path, json=payload)
    assert response.status_code == 401


class TestIcsExport:
    def test_success_with_course_code(self, authenticated_client: TestClient) -> None:
        with patch(
            "app.routers.export.create_ics",
            return_value="BEGIN:VCALENDAR\r\nEND:VCALENDAR",
        ):
            response = authenticated_client.post("/export/ics", json=_ics_payload())

        assert response.status_code == 200
        assert "text/calendar" in response.headers["content-type"]
        assert (
            'filename="Syllabuddy - CSC413.ics"'
            in response.headers["content-disposition"]
        )

    def test_empty_events_returns_400(self, authenticated_client: TestClient) -> None:
        payload = _ics_payload()
        payload["events"] = []
        response = authenticated_client.post("/export/ics", json=payload)
        assert response.status_code == 400
        assert response.json()["detail"] == "No events to export"

    def test_missing_course_code_returns_400(
        self,
        authenticated_client: TestClient,
    ) -> None:
        payload = _ics_payload()
        payload["events"] = [
            {
                "title": "Event Without Course",
                "due_date": "2024-01-15T23:59:00",
                "course": "",
                "event_type": "assignment",
                "description": "",
                "time_specified": True,
            }
        ]
        response = authenticated_client.post("/export/ics", json=payload)

        assert response.status_code == 400
        assert response.json()["detail"] == "Course code(s) missing"

    def test_mixed_courses_returns_400(self, authenticated_client: TestClient) -> None:
        payload = _ics_payload()
        payload["events"] = [
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
        ]
        response = authenticated_client.post("/export/ics", json=payload)

        assert response.status_code == 400
        assert "Mixed courses" in response.json()["detail"]

    def test_uses_course_name_in_calendar_name(
        self,
        authenticated_client: TestClient,
    ) -> None:
        response = authenticated_client.post("/export/ics", json=_ics_payload())

        assert response.status_code == 200
        assert (
            'filename="Syllabuddy - CSC413.ics"'
            in response.headers["content-disposition"]
        )
        assert "X-WR-CALNAME:Syllabuddy - CSC413" in response.text


class TestOutlookExport:
    def test_single_event_returns_ics(self, authenticated_client: TestClient) -> None:
        response = authenticated_client.post("/export/outlook", json=_outlook_payload())

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/calendar; charset=utf-8"
        assert (
            'filename="Syllabuddy - CSC413.ics"'
            in response.headers["content-disposition"]
        )

    def test_multiple_events_returns_ics(self, authenticated_client: TestClient) -> None:
        payload = _outlook_payload()
        payload["events"] = [
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
        ]

        response = authenticated_client.post("/export/outlook", json=payload)

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/calendar; charset=utf-8"
        assert (
            'filename="Syllabuddy - CSC413.ics"'
            in response.headers["content-disposition"]
        )

    def test_empty_events_returns_400(self, authenticated_client: TestClient) -> None:
        payload = _outlook_payload()
        payload["events"] = []
        response = authenticated_client.post("/export/outlook", json=payload)
        assert response.status_code == 400
        assert response.json()["detail"] == "No events to export"

    def test_missing_course_code_returns_400(
        self,
        authenticated_client: TestClient,
    ) -> None:
        payload = _outlook_payload()
        payload["events"] = [
            {
                "title": "Event Without Course",
                "due_date": "2024-01-15T23:59:00",
                "course": "",
                "event_type": "assignment",
                "description": "",
                "time_specified": True,
            }
        ]

        response = authenticated_client.post("/export/outlook", json=payload)

        assert response.status_code == 400
        assert response.json()["detail"] == "Course code(s) missing"

    def test_mixed_courses_returns_400(self, authenticated_client: TestClient) -> None:
        payload = _outlook_payload()
        payload["events"] = [
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
        ]

        response = authenticated_client.post("/export/outlook", json=payload)

        assert response.status_code == 400
        assert "Mixed courses" in response.json()["detail"]


class TestGoogleExport:
    def test_requires_access_token(self, authenticated_client: TestClient) -> None:
        payload = _google_payload()
        payload.pop("access_token")

        response = authenticated_client.post("/export/google", json=payload)
        assert response.status_code == 400
        assert response.json()["detail"] == "Access token required"

    def test_success_returns_calendar_name(
        self,
        authenticated_client: TestClient,
    ) -> None:
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
            response = authenticated_client.post("/export/google", json=_google_payload())

        assert response.status_code == 200
        assert response.json()["created_count"] == 1
        assert response.json()["calendar_name"] == "Syllabuddy - CSC413"

    def test_empty_events_returns_400(self, authenticated_client: TestClient) -> None:
        payload = _google_payload()
        payload["events"] = []

        response = authenticated_client.post("/export/google", json=payload)
        assert response.status_code == 400
        assert response.json()["detail"] == "No events to export"

    def test_missing_course_code_returns_400(
        self,
        authenticated_client: TestClient,
    ) -> None:
        payload = _google_payload()
        payload["events"] = [
            {
                "title": "Event Without Course",
                "due_date": "2024-01-15T23:59:00",
                "course": "",
                "event_type": "assignment",
                "description": "",
                "time_specified": True,
            }
        ]

        with patch(
            "app.routers.export.export_to_google_calendar_sync",
            side_effect=__import__(
                "app.services.calendar_utils",
                fromlist=["MissingCourseCodeError"],
            ).MissingCourseCodeError(),
        ):
            response = authenticated_client.post("/export/google", json=payload)

        assert response.status_code == 400
        assert response.json()["detail"] == "Course code(s) missing"

    def test_mixed_courses_returns_400(self, authenticated_client: TestClient) -> None:
        payload = _google_payload()
        payload["events"] = [
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
        ]

        with patch(
            "app.routers.export.export_to_google_calendar_sync",
            side_effect=__import__(
                "app.services.calendar_utils",
                fromlist=["MixedCourseError"],
            ).MixedCourseError({"CSC413", "CSC420"}),
        ):
            response = authenticated_client.post("/export/google", json=payload)

        assert response.status_code == 400
        assert "Mixed courses" in response.json()["detail"]

    def test_api_failure_returns_502(self, authenticated_client: TestClient) -> None:
        with patch(
            "app.routers.export.export_to_google_calendar_sync",
            side_effect=RuntimeError("upstream failed"),
        ):
            response = authenticated_client.post("/export/google", json=_google_payload())

        assert response.status_code == 502
        assert "Google Calendar error" in response.json()["detail"]
