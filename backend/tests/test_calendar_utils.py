import pytest
from datetime import datetime

from app.services.calendar_utils import (
    validate_and_get_course_code,
    get_calendar_name,
    sanitize_filename,
    MissingCourseCodeError,
    MixedCourseError,
)
from app.models.schemas import ParsedEvent


class TestValidateAndGetCourseCode:
    def test_returns_uppercase_course_code(self):
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
                course="CSC413",
                type="assignment",
            ),
        ]

        result = validate_and_get_course_code(events)

        assert result == "CSC413"

    def test_raises_error_for_empty_course(self):
        events = [
            ParsedEvent(
                title="Event",
                due_date=datetime(2024, 1, 15),
                course="",
                type="assignment",
            ),
        ]

        with pytest.raises(MissingCourseCodeError, match="Course code\\(s\\) missing"):
            validate_and_get_course_code(events)

    def test_raises_error_for_whitespace_only_course(self):
        events = [
            ParsedEvent(
                title="Event",
                due_date=datetime(2024, 1, 15),
                course="   ",
                type="assignment",
            ),
        ]

        with pytest.raises(MissingCourseCodeError):
            validate_and_get_course_code(events)

    def test_raises_error_when_any_event_missing_course(self):
        events = [
            ParsedEvent(
                title="Good Event",
                due_date=datetime(2024, 1, 15),
                course="CSC413",
                type="assignment",
            ),
            ParsedEvent(
                title="Bad Event",
                due_date=datetime(2024, 1, 16),
                course="",
                type="assignment",
            ),
        ]

        with pytest.raises(MissingCourseCodeError):
            validate_and_get_course_code(events)

    def test_raises_value_error_for_empty_list(self):
        with pytest.raises(ValueError, match="No events to export"):
            validate_and_get_course_code([])

    def test_strips_whitespace_from_course(self):
        events = [
            ParsedEvent(
                title="HW1",
                due_date=datetime(2024, 1, 15),
                course="  CSC413  ",
                type="assignment",
            ),
        ]

        result = validate_and_get_course_code(events)

        assert result == "CSC413"

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

        with pytest.raises(MixedCourseError) as exc_info:
            validate_and_get_course_code(events)

        assert "CSC413" in str(exc_info.value)
        assert "CSC420" in str(exc_info.value)

    def test_normalizes_case_for_comparison(self):
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
                course="csc413",
                type="assignment",
            ),
            ParsedEvent(
                title="HW3",
                due_date=datetime(2024, 1, 25),
                course="  CSC413  ",
                type="assignment",
            ),
        ]

        result = validate_and_get_course_code(events)

        assert result == "CSC413"

    def test_returns_uppercase_regardless_of_input(self):
        events = [
            ParsedEvent(
                title="HW1",
                due_date=datetime(2024, 1, 15),
                course="csc413",
                type="assignment",
            ),
        ]

        result = validate_and_get_course_code(events)

        assert result == "CSC413"


class TestGetCalendarName:
    def test_adds_syllabuddy_prefix(self):
        result = get_calendar_name("CSC413")
        assert result == "Syllabuddy - CSC413"


class TestSanitizeFilename:
    def test_keeps_alphanumeric_and_safe_chars(self):
        result = sanitize_filename("Syllabuddy - CSC413")
        assert result == "Syllabuddy - CSC413"

    def test_removes_quotes(self):
        result = sanitize_filename('CS"101')
        assert result == "CS101"

    def test_removes_semicolons(self):
        result = sanitize_filename("MATH;101")
        assert result == "MATH101"

    def test_removes_backslashes(self):
        result = sanitize_filename("CS\\101")
        assert result == "CS101"

    def test_replaces_newlines_with_space(self):
        result = sanitize_filename("CS101\nDROP")
        assert result == "CS101 DROP"

    def test_collapses_multiple_spaces(self):
        result = sanitize_filename("CS   101")
        assert result == "CS 101"

    def test_returns_fallback_for_empty_result(self):
        result = sanitize_filename('";\\')
        assert result == "calendar"
