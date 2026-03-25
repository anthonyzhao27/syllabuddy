"""Endpoint tests for export router behavior."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_export_ics_success():
    payload = {
        "events": [
            {
                "title": "Homework 1",
                "due_date": "2025-01-30T23:59:00",
                "course": "CS 101",
                "event_type": "assignment",
                "description": "",
                "time_specified": False,
            }
        ],
        "filename": "syllabus.ics",
        "timezone": "America/Toronto",
    }

    with patch(
        "app.routers.export.create_ics", return_value="BEGIN:VCALENDAR\r\nEND:VCALENDAR"
    ):
        response = client.post("/export/ics", json=payload)

    assert response.status_code == 200
    assert "text/calendar" in response.headers["content-type"]
    assert 'filename="syllabus.ics"' in response.headers["content-disposition"]


def test_export_ics_empty_events():
    response = client.post(
        "/export/ics",
        json={"events": [], "filename": "syllabus.ics", "timezone": "America/Toronto"},
    )
    assert response.status_code == 400


def test_export_outlook_single_event_returns_deep_link_json():
    payload = {
        "events": [
            {
                "title": "Midterm",
                "due_date": "2025-03-10T14:00:00",
                "course": "CS 101",
                "event_type": "exam",
                "description": "",
                "time_specified": True,
            }
        ],
        "timezone": "America/Toronto",
    }

    with patch(
        "app.routers.export.generate_outlook_deep_link",
        return_value="https://outlook.office.com/calendar/0/deeplink/compose",
    ):
        response = client.post("/export/outlook", json=payload)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["method"] == "deep_link"


def test_export_outlook_multiple_events_returns_ics():
    payload = {
        "events": [
            {
                "title": "Homework 1",
                "due_date": "2025-01-30T23:59:00",
                "course": "CS 101",
                "event_type": "assignment",
                "description": "",
                "time_specified": False,
            },
            {
                "title": "Quiz 1",
                "due_date": "2025-02-10T10:00:00",
                "course": "CS 101",
                "event_type": "quiz",
                "description": "",
                "time_specified": True,
            },
        ],
        "timezone": "America/Toronto",
    }

    with patch(
        "app.routers.export.create_ics", return_value="BEGIN:VCALENDAR\r\nEND:VCALENDAR"
    ):
        response = client.post("/export/outlook", json=payload)

    assert response.status_code == 200
    assert "text/calendar" in response.headers["content-type"]
    assert 'filename="syllabus-outlook.ics"' in response.headers["content-disposition"]


def test_export_google_requires_access_token():
    payload = {
        "events": [
            {
                "title": "Homework 1",
                "due_date": "2025-01-30T23:59:00",
                "course": "CS 101",
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


def test_export_google_success():
    payload = {
        "events": [
            {
                "title": "Homework 1",
                "due_date": "2025-01-30T23:59:00",
                "course": "CS 101",
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
        },
    ):
        response = client.post("/export/google", json=payload)

    assert response.status_code == 200
    assert response.json()["created_count"] == 1


def test_export_google_failure_returns_502():
    payload = {
        "events": [
            {
                "title": "Homework 1",
                "due_date": "2025-01-30T23:59:00",
                "course": "CS 101",
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
