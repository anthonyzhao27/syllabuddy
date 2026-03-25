"""Tests for Outlook export service."""

from datetime import datetime
from urllib.parse import parse_qs, urlparse

from app.models.schemas import ParsedEvent
from app.services.outlook import generate_outlook_deep_link


class TestGenerateOutlookDeepLink:
    def test_generates_valid_url(self):
        event = ParsedEvent(
            title="Homework 1",
            due_date=datetime(2025, 1, 30, 14, 0),
            course="CS 101",
        )
        url = generate_outlook_deep_link(event, "America/Toronto")

        parsed = urlparse(url)
        assert parsed.scheme == "https"
        assert parsed.netloc == "outlook.office.com"
        assert "/calendar/0/deeplink/compose" in parsed.path

    def test_includes_subject_with_course(self):
        event = ParsedEvent(
            title="Midterm",
            due_date=datetime(2025, 3, 10, 14, 0),
            course="MATH 200",
        )
        url = generate_outlook_deep_link(event, "America/Toronto")

        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        assert "[MATH 200] Midterm" in params["subject"][0]

    def test_all_day_event(self):
        event = ParsedEvent(
            title="Project Due",
            due_date=datetime(2025, 4, 15, 23, 59),
            time_specified=False,
        )
        url = generate_outlook_deep_link(event, "America/Toronto")

        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        assert params["allday"][0] == "true"

    def test_timed_event(self):
        event = ParsedEvent(
            title="Office Hours",
            due_date=datetime(2025, 2, 20, 10, 30),
        )
        url = generate_outlook_deep_link(event, "America/Toronto")

        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        assert params["allday"][0] == "false"

    def test_includes_description(self):
        event = ParsedEvent(
            title="Quiz",
            due_date=datetime(2025, 2, 10, 9, 0),
            description="Covers chapters 1-3",
        )
        url = generate_outlook_deep_link(event, "America/Toronto")

        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        assert "Covers chapters 1-3" in params["body"][0]
