"""Shared utilities for calendar export services."""

import re

from app.models.schemas import ParsedEvent

CALENDAR_NAME_PREFIX = "Syllabuddy - "


class MissingCourseCodeError(Exception):
    """Raised when events are missing course codes."""

    def __init__(self):
        super().__init__("Course code(s) missing")


class MixedCourseError(Exception):
    """Raised when events have different course codes."""

    def __init__(self, courses: set[str]):
        self.courses = courses
        super().__init__(f"Mixed courses not supported: {', '.join(sorted(courses))}")


def validate_and_get_course_code(events: list[ParsedEvent]) -> str:
    """
    Validate all events have the same course code and return it (normalized).

    Args:
        events: List of events to validate.

    Returns:
        The course code, normalized to uppercase (e.g., "CSC413").

    Raises:
        MissingCourseCodeError: If any event is missing a course code.
        MixedCourseError: If events have different course codes.
        ValueError: If events list is empty.
    """
    if not events:
        raise ValueError("No events to export")

    has_missing = any(not e.course or not e.course.strip() for e in events)
    if has_missing:
        raise MissingCourseCodeError()

    normalized_courses = {e.course.strip().upper() for e in events}

    if len(normalized_courses) > 1:
        raise MixedCourseError(normalized_courses)

    return normalized_courses.pop()


def get_calendar_name(course_code: str) -> str:
    """
    Generate the calendar name for a course code.

    Args:
        course_code: The course code (e.g., "CSC413").

    Returns:
        Calendar name in format "Syllabuddy - {course_code}".
    """
    return f"{CALENDAR_NAME_PREFIX}{course_code}"


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string for safe use in Content-Disposition filenames.

    Args:
        name: The raw filename (without extension).

    Returns:
        Sanitized filename safe for Content-Disposition headers.
    """
    sanitized = re.sub(r"[^a-zA-Z0-9\s\-_]", "", name)
    sanitized = re.sub(r"\s+", " ", sanitized).strip()
    return sanitized or "calendar"
