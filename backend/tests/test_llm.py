"""Tests for LLM extraction service."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.schemas import EventType, ParsedEvent
from app.services.llm import (
    MAX_PROMPT_CHARS,
    OPENAI_TIMEOUT_SECONDS,
    _apply_all_smart_defaults,
    _apply_smart_defaults,
    _parse_events,
    _parse_duration,
    _parse_extraction_result,
    extract_events,
)


class TestParseEvents:
    def test_parses_valid_array(self) -> None:
        raw = json.dumps(
            [
                {
                    "title": "Homework 1",
                    "due_date": "2025-01-30T23:59:00",
                    "course": "CS 101",
                    "event_type": "assignment",
                    "description": "",
                }
            ]
        )
        events = _parse_events(raw)
        assert len(events) == 1
        assert events[0].title == "Homework 1"
        assert events[0].due_date == datetime(2025, 1, 30, 23, 59)
        assert events[0].course == "CS 101"
        assert events[0].event_type == "assignment"

    def test_parses_object_with_events_key(self) -> None:
        raw = json.dumps(
            {
                "events": [
                    {
                        "title": "Midterm",
                        "due_date": "2025-03-10T14:00:00",
                        "course": "CS 101",
                        "event_type": "exam",
                        "description": "Covers chapters 1-5",
                    }
                ]
            }
        )
        events = _parse_events(raw)
        assert len(events) == 1
        assert events[0].title == "Midterm"
        assert events[0].event_type == "exam"

    def test_parses_object_with_arbitrary_key(self) -> None:
        raw = json.dumps(
            {
                "assignments": [
                    {
                        "title": "Quiz 1",
                        "due_date": "2025-02-14T23:59:00",
                        "event_type": "quiz",
                    }
                ]
            }
        )
        events = _parse_events(raw)
        assert len(events) == 1

    def test_strips_markdown_fences(self) -> None:
        raw = '```json\n[{"title": "HW1", "due_date": "2025-01-30T23:59:00"}]\n```'
        events = _parse_events(raw)
        assert len(events) == 1
        assert events[0].title == "HW1"

    def test_skips_malformed_events(self) -> None:
        raw = json.dumps(
            [
                {"title": "Good Event", "due_date": "2025-01-30T23:59:00"},
                {"title": "Bad Event", "due_date": "not-a-date"},
                {"title": "Also Good", "due_date": "2025-03-10T14:00:00"},
            ]
        )
        events = _parse_events(raw)
        assert len(events) == 2
        assert events[0].title == "Good Event"
        assert events[1].title == "Also Good"

    def test_empty_array(self) -> None:
        events = _parse_events("[]")
        assert events == []

    def test_empty_object_with_array(self) -> None:
        events = _parse_events('{"events": []}')
        assert events == []

    def test_optional_fields_default(self) -> None:
        raw = json.dumps([{"title": "HW1", "due_date": "2025-01-30T23:59:00"}])
        events = _parse_events(raw)
        assert events[0].course == ""
        assert events[0].event_type == EventType.OTHER
        assert events[0].description == ""

    def test_raises_on_total_garbage(self) -> None:
        with pytest.raises(ValueError, match="Could not parse"):
            _parse_events("this is not json at all")

    def test_raises_on_object_without_array(self) -> None:
        with pytest.raises(ValueError, match="no array field"):
            _parse_events('{"status": "ok"}')


class TestExtractEvents:
    @pytest.mark.asyncio
    async def test_calls_openai_and_returns_events(self) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "events": [
                    {
                        "title": "Homework 1",
                        "due_date": "2025-01-30T23:59:00",
                        "course": "CS 101",
                        "event_type": "assignment",
                        "description": "Ch 1-3",
                    },
                    {
                        "title": "Midterm",
                        "due_date": "2025-03-10T14:00:00",
                        "course": "CS 101",
                        "event_type": "exam",
                        "description": "",
                    },
                ],
                "recurring_events": [],
            }
        )

        with patch("app.services.llm.AsyncOpenAI") as MockClient:
            instance = AsyncMock()
            instance.chat.completions.create = AsyncMock(return_value=mock_response)
            MockClient.return_value = instance

            events = await extract_events("Homework 1 due Jan 30. Midterm March 10.")

            assert len(events) == 2
            assert events[0].title == "Homework 1"
            assert events[1].title == "Midterm"

            call_kwargs = instance.chat.completions.create.call_args.kwargs
            assert call_kwargs["response_format"] == {"type": "json_object"}
            assert call_kwargs["temperature"] == 0.0
            assert len(call_kwargs["messages"]) == 2
            assert call_kwargs["messages"][1]["content"] == (
                "Homework 1 due Jan 30. Midterm March 10."
            )

    @pytest.mark.asyncio
    async def test_empty_response_returns_empty_list(self) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"events": []}'

        with patch("app.services.llm.AsyncOpenAI") as MockClient:
            instance = AsyncMock()
            instance.chat.completions.create = AsyncMock(return_value=mock_response)
            MockClient.return_value = instance

            events = await extract_events("This syllabus has no dates.")
            assert events == []

    @pytest.mark.asyncio
    async def test_raises_on_api_failure(self) -> None:
        with patch("app.services.llm.AsyncOpenAI") as MockClient:
            instance = AsyncMock()
            instance.chat.completions.create = AsyncMock(
                side_effect=Exception("API rate limit")
            )
            MockClient.return_value = instance

            with pytest.raises(Exception, match="API rate limit"):
                await extract_events("some text")

    @pytest.mark.asyncio
    async def test_raises_value_error_on_bad_json(self) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "not json"

        with patch("app.services.llm.AsyncOpenAI") as MockClient:
            instance = AsyncMock()
            instance.chat.completions.create = AsyncMock(return_value=mock_response)
            MockClient.return_value = instance

            with pytest.raises(ValueError):
                await extract_events("some text")


class TestParseDuration:
    def test_positive_integer(self):
        assert _parse_duration(120) == 120

    def test_positive_integer_string(self):
        assert _parse_duration("90") == 90

    def test_positive_float_truncates(self):
        assert _parse_duration(90.5) == 90

    def test_hours(self):
        assert _parse_duration("2 hours") == 120

    def test_hour_singular(self):
        assert _parse_duration("1 hour") == 60

    def test_hrs_abbreviation(self):
        assert _parse_duration("2 hrs") == 120

    def test_h_abbreviation(self):
        assert _parse_duration("2h") == 120

    def test_minutes(self):
        assert _parse_duration("90 minutes") == 90

    def test_min_abbreviation(self):
        assert _parse_duration("45 min") == 45

    def test_mins_abbreviation(self):
        assert _parse_duration("30 mins") == 30

    def test_fractional_hours(self):
        assert _parse_duration("1.5 hours") == 90

    def test_whitespace_tolerance(self):
        assert _parse_duration("  2  hours  ") == 120

    def test_zero_returns_none(self):
        assert _parse_duration(0) is None

    def test_negative_returns_none(self):
        assert _parse_duration(-30) is None

    def test_zero_string_returns_none(self):
        assert _parse_duration("0") is None

    def test_none_returns_none(self):
        assert _parse_duration(None) is None

    def test_garbage_string_returns_none(self):
        assert _parse_duration("sometime") is None

    def test_empty_string_returns_none(self):
        assert _parse_duration("") is None


class TestSmartDefaults:
    def test_preserves_explicit_duration(self):
        event = ParsedEvent(
            title="Midterm",
            due_date=datetime(2025, 2, 15, 14, 0),
            event_type=EventType.EXAM,
            time_specified=True,
            duration_minutes=120,
        )
        result = _apply_smart_defaults(event)
        assert result.duration_minutes == 120
        assert result.due_date == datetime(2025, 2, 15, 14, 0)

    def test_all_day_no_duration(self):
        event = ParsedEvent(
            title="Homework 1",
            due_date=datetime(2025, 1, 30, 23, 59),
            event_type=EventType.ASSIGNMENT,
            time_specified=False,
            duration_minutes=None,
        )
        result = _apply_smart_defaults(event)
        assert result.duration_minutes is None
        assert result.due_date == datetime(2025, 1, 30, 23, 59)

    def test_2359_deadline_adjusted(self):
        event = ParsedEvent(
            title="Homework 1",
            due_date=datetime(2025, 1, 30, 23, 59, 0),
            event_type=EventType.ASSIGNMENT,
            time_specified=True,
            duration_minutes=None,
        )
        result = _apply_smart_defaults(event)
        assert result.due_date == datetime(2025, 1, 30, 23, 30, 0)
        assert result.duration_minutes == 30

    def test_2359_exam_not_adjusted(self):
        event = ParsedEvent(
            title="Late Night Exam",
            due_date=datetime(2025, 1, 30, 23, 59, 0),
            event_type=EventType.EXAM,
            time_specified=True,
            duration_minutes=None,
        )
        result = _apply_smart_defaults(event)
        assert result.due_date == datetime(2025, 1, 30, 23, 59, 0)
        assert result.duration_minutes == 120

    def test_2358_not_adjusted(self):
        event = ParsedEvent(
            title="Homework",
            due_date=datetime(2025, 1, 30, 23, 58, 0),
            event_type=EventType.ASSIGNMENT,
            time_specified=True,
            duration_minutes=None,
        )
        result = _apply_smart_defaults(event)
        assert result.due_date == datetime(2025, 1, 30, 23, 58, 0)
        assert result.duration_minutes == 30

    def test_exam_default_duration(self):
        event = ParsedEvent(
            title="Midterm",
            due_date=datetime(2025, 2, 15, 14, 0),
            event_type=EventType.EXAM,
            time_specified=True,
            duration_minutes=None,
        )
        result = _apply_smart_defaults(event)
        assert result.duration_minutes == 120

    def test_quiz_default_duration(self):
        event = ParsedEvent(
            title="Quiz 1",
            due_date=datetime(2025, 1, 17, 10, 0),
            event_type=EventType.QUIZ,
            time_specified=True,
            duration_minutes=None,
        )
        result = _apply_smart_defaults(event)
        assert result.duration_minutes == 30

    def test_presentation_default_duration(self):
        event = ParsedEvent(
            title="Final Presentation",
            due_date=datetime(2025, 4, 10, 14, 0),
            event_type=EventType.PRESENTATION,
            time_specified=True,
            duration_minutes=None,
        )
        result = _apply_smart_defaults(event)
        assert result.duration_minutes == 30

    def test_assignment_default_duration(self):
        event = ParsedEvent(
            title="Project Milestone",
            due_date=datetime(2025, 3, 1, 17, 0),
            event_type=EventType.ASSIGNMENT,
            time_specified=True,
            duration_minutes=None,
        )
        result = _apply_smart_defaults(event)
        assert result.duration_minutes == 30


class TestApplyAllSmartDefaults:
    def test_applies_to_all_events(self):
        events = [
            ParsedEvent(
                title="Exam",
                due_date=datetime(2025, 2, 15, 14, 0),
                event_type=EventType.EXAM,
                time_specified=True,
                duration_minutes=None,
            ),
            ParsedEvent(
                title="Quiz",
                due_date=datetime(2025, 1, 17, 10, 0),
                event_type=EventType.QUIZ,
                time_specified=True,
                duration_minutes=None,
            ),
        ]
        results = _apply_all_smart_defaults(events)
        assert results[0].duration_minutes == 120
        assert results[1].duration_minutes == 30


class TestExtractEventsPostProcessing:
    @pytest.mark.asyncio
    async def test_duration_preserved_from_llm(self):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "events": [
                    {
                        "title": "Midterm",
                        "due_date": "2025-02-15T14:00:00",
                        "event_type": "exam",
                        "time_specified": True,
                        "duration_minutes": 120,
                    }
                ]
            }
        )

        with patch("app.services.llm.AsyncOpenAI") as MockClient:
            instance = AsyncMock()
            instance.chat.completions.create = AsyncMock(return_value=mock_response)
            MockClient.return_value = instance

            events = await extract_events("Midterm on Feb 15, 2 hours")

            assert len(events) == 1
            assert events[0].duration_minutes == 120
            assert events[0].due_date.hour == 14
            assert events[0].due_date.minute == 0

    @pytest.mark.asyncio
    async def test_natural_language_duration_parsed(self):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "events": [
                    {
                        "title": "Midterm",
                        "due_date": "2025-02-15T14:00:00",
                        "event_type": "exam",
                        "time_specified": True,
                        "duration_minutes": "2 hours",
                    }
                ]
            }
        )

        with patch("app.services.llm.AsyncOpenAI") as MockClient:
            instance = AsyncMock()
            instance.chat.completions.create = AsyncMock(return_value=mock_response)
            MockClient.return_value = instance

            events = await extract_events("Midterm, 2 hours")

            assert events[0].duration_minutes == 120

    @pytest.mark.asyncio
    async def test_2359_deadline_adjusted(self):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "events": [
                    {
                        "title": "Homework 1",
                        "due_date": "2025-01-30T23:59:00",
                        "event_type": "assignment",
                        "time_specified": True,
                        "duration_minutes": None,
                    }
                ]
            }
        )

        with patch("app.services.llm.AsyncOpenAI") as MockClient:
            instance = AsyncMock()
            instance.chat.completions.create = AsyncMock(return_value=mock_response)
            MockClient.return_value = instance

            events = await extract_events("HW1 due Jan 30 at 11:59 PM")

            assert len(events) == 1
            assert events[0].due_date.hour == 23
            assert events[0].due_date.minute == 30
            assert events[0].duration_minutes == 30

    @pytest.mark.asyncio
    async def test_zero_duration_normalized_to_default(self):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "events": [
                    {
                        "title": "Quiz",
                        "due_date": "2025-01-17T10:00:00",
                        "event_type": "quiz",
                        "time_specified": True,
                        "duration_minutes": 0,
                    }
                ]
            }
        )

        with patch("app.services.llm.AsyncOpenAI") as MockClient:
            instance = AsyncMock()
            instance.chat.completions.create = AsyncMock(return_value=mock_response)
            MockClient.return_value = instance

            events = await extract_events("Quiz")

            assert events[0].duration_minutes == 30


class TestParseExtractionResult:
    def test_parses_events_and_recurring_events(self):
        raw = json.dumps(
            {
                "events": [
                    {
                        "title": "Midterm",
                        "due_date": "2025-02-15T14:00:00",
                        "event_type": "exam",
                        "time_specified": True,
                        "duration_minutes": 120,
                    }
                ],
                "recurring_events": [
                    {
                        "title": "Friday Quiz",
                        "event_type": "quiz",
                        "recurrence": {
                            "frequency": "weekly",
                            "weekday": "friday",
                            "start_date": "2025-01-10",
                            "end_date": "2025-01-24",
                        },
                    }
                ],
            }
        )

        result = _parse_extraction_result(raw)

        assert len(result.events) == 1
        assert result.events[0].title == "Midterm"
        assert len(result.recurring_events) == 1
        assert result.recurring_events[0].title == "Friday Quiz"

    def test_skips_malformed_recurring_event(self):
        raw = json.dumps(
            {
                "events": [],
                "recurring_events": [
                    {
                        "title": "Valid Quiz",
                        "event_type": "quiz",
                        "recurrence": {
                            "frequency": "weekly",
                            "weekday": "friday",
                            "start_date": "2025-01-10",
                            "end_date": "2025-01-24",
                        },
                    },
                    {
                        "title": "Invalid Quiz",
                        "event_type": "quiz",
                        "recurrence": {
                            "frequency": "weekly",
                        },
                    },
                ],
            }
        )

        result = _parse_extraction_result(raw)

        assert len(result.recurring_events) == 1
        assert result.recurring_events[0].title == "Valid Quiz"


class TestExtractEventsWithRecurrence:
    @pytest.mark.asyncio
    async def test_recurring_event_expanded(self):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "events": [],
                "recurring_events": [
                    {
                        "title": "Friday Quiz",
                        "course": "CS 101",
                        "event_type": "quiz",
                        "recurrence": {
                            "frequency": "weekly",
                            "weekday": "friday",
                            "start_date": "2025-01-10",
                            "end_date": "2025-01-31",
                            "time": "10:00:00",
                            "exclusions": [],
                        },
                    }
                ],
            }
        )

        with patch("app.services.llm.AsyncOpenAI") as MockClient:
            instance = AsyncMock()
            instance.chat.completions.create = AsyncMock(return_value=mock_response)
            MockClient.return_value = instance

            events = await extract_events("Weekly quiz every Friday")

            assert len(events) == 4

            for event in events:
                assert event.due_date.weekday() == 4

            assert events[0].due_date.date() == datetime(2025, 1, 10).date()
            assert events[3].due_date.date() == datetime(2025, 1, 31).date()

    @pytest.mark.asyncio
    async def test_mixed_events_and_recurring(self):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "events": [
                    {
                        "title": "Midterm",
                        "due_date": "2025-02-15T14:00:00",
                        "event_type": "exam",
                        "time_specified": True,
                        "duration_minutes": 120,
                    }
                ],
                "recurring_events": [
                    {
                        "title": "Quiz",
                        "event_type": "quiz",
                        "recurrence": {
                            "frequency": "weekly",
                            "weekday": "friday",
                            "start_date": "2025-01-10",
                            "end_date": "2025-01-24",
                        },
                    }
                ],
            }
        )

        with patch("app.services.llm.AsyncOpenAI") as MockClient:
            instance = AsyncMock()
            instance.chat.completions.create = AsyncMock(return_value=mock_response)
            MockClient.return_value = instance

            events = await extract_events("...")

            assert len(events) == 4

            midterm = next(e for e in events if "Midterm" in e.title)
            assert midterm.duration_minutes == 120

            quizzes = [e for e in events if "Quiz" in e.title]
            assert len(quizzes) == 3


class TestCostAndTimeoutGuards:
    @pytest.mark.asyncio
    async def test_oversized_text_is_capped(self) -> None:
        """Text longer than MAX_PROMPT_CHARS is truncated before sending."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"events": []}'

        oversized = "x" * (MAX_PROMPT_CHARS + 5_000)

        with patch("app.services.llm.AsyncOpenAI") as MockClient:
            instance = AsyncMock()
            instance.chat.completions.create = AsyncMock(return_value=mock_response)
            MockClient.return_value = instance

            await extract_events(oversized)

            call_kwargs = instance.chat.completions.create.call_args.kwargs
            sent_text = call_kwargs["messages"][1]["content"]
            assert len(sent_text) == MAX_PROMPT_CHARS

    @pytest.mark.asyncio
    async def test_text_under_cap_not_truncated(self) -> None:
        """Text within the cap is passed through unchanged."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"events": []}'

        text = "Homework 1 due Jan 30."

        with patch("app.services.llm.AsyncOpenAI") as MockClient:
            instance = AsyncMock()
            instance.chat.completions.create = AsyncMock(return_value=mock_response)
            MockClient.return_value = instance

            await extract_events(text)

            call_kwargs = instance.chat.completions.create.call_args.kwargs
            assert call_kwargs["messages"][1]["content"] == text

    @pytest.mark.asyncio
    async def test_client_built_with_timeout(self) -> None:
        """The OpenAI client is constructed with an explicit timeout."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"events": []}'

        with patch("app.services.llm.AsyncOpenAI") as MockClient:
            instance = AsyncMock()
            instance.chat.completions.create = AsyncMock(return_value=mock_response)
            MockClient.return_value = instance

            await extract_events("some text")

            timeout = MockClient.call_args.kwargs["timeout"]
            assert timeout == OPENAI_TIMEOUT_SECONDS

    def test_timeout_is_bounded(self) -> None:
        """Timeout is well under the SDK's 600s default."""
        assert 0 < OPENAI_TIMEOUT_SECONDS < 600


# ---------------------------------------------------------------------------
# Transcribe-then-resolve pipeline (extract_syllabus)
# ---------------------------------------------------------------------------

_TRANSCRIPTION = {
    "course_code": "CSC263H1S",
    "term": {"season": "winter", "year": 2026, "campus": "st_george", "evidence": ""},
    "schedule_anchor": {
        "week1_month": None,
        "week1_day": None,
        "evidence": "",
        "reading_week_numbered": None,
    },
    "meetings": [],
    "week_dates": [],
    "events": [
        {
            "title": "Quiz 1",
            "event_type": "quiz",
            "description": "",
            "date_kind": "week",
            "date": None,
            "stated_weekday": "wednesday",
            "week": 3,
            "in_class": False,
            "meeting_kind": None,
            "time": None,
            "duration_minutes": None,
            "source_text": "Week 3: Quiz 1",
        }
    ],
    "recurring": [],
}


def _mock_client(content: str) -> MagicMock:
    client = MagicMock()
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    client.chat.completions.create = AsyncMock(return_value=response)
    return client


class TestExtractSyllabus:
    @pytest.mark.asyncio
    async def test_uses_strict_schema_and_injects_upload_date(self) -> None:
        from datetime import date

        from app.services.llm import extract_syllabus

        client = _mock_client(json.dumps(_TRANSCRIPTION))
        with patch("app.services.llm.AsyncOpenAI", return_value=client):
            await extract_syllabus("Week 3: Quiz 1", today=date(2025, 12, 29))

        kwargs = client.chat.completions.create.await_args.kwargs
        assert kwargs["response_format"]["type"] == "json_schema"
        assert kwargs["response_format"]["json_schema"]["strict"] is True
        assert kwargs["messages"][1]["content"].startswith(
            "Upload date: 2025-12-29 (Monday)"
        )
        assert kwargs["temperature"] == 0.0

    @pytest.mark.asyncio
    async def test_reasoning_models_get_reasoning_params(self) -> None:
        from datetime import date

        from app.services.llm import extract_syllabus

        client = _mock_client(json.dumps(_TRANSCRIPTION))
        with patch("app.services.llm.AsyncOpenAI", return_value=client):
            await extract_syllabus("x", today=date(2025, 12, 29), model="gpt-5.6-luna")

        kwargs = client.chat.completions.create.await_args.kwargs
        assert "temperature" not in kwargs
        assert kwargs["reasoning_effort"] == "low"
        assert "max_completion_tokens" in kwargs

    @pytest.mark.asyncio
    async def test_grounding_applied_and_dates_resolved(self) -> None:
        from datetime import date

        from app.services.llm import extract_syllabus

        client = _mock_client(json.dumps(_TRANSCRIPTION))
        with patch("app.services.llm.AsyncOpenAI", return_value=client):
            outcome = await extract_syllabus(
                "Schedule\nWeek 3: Quiz 1\n", today=date(2025, 12, 29)
            )

        # "wednesday" is not printed anywhere -> dropped -> Monday of week 3
        assert outcome.extraction.events[0].stated_weekday is None
        assert outcome.events[0].due_date.date().weekday() == 0
        assert outcome.events[0].date_confidence == "estimated"
        assert outcome.term_context.term_id == "2026W"

    @pytest.mark.asyncio
    async def test_invalid_json_raises_value_error(self) -> None:
        from datetime import date

        from app.services.llm import extract_syllabus

        client = _mock_client("not json")
        with patch("app.services.llm.AsyncOpenAI", return_value=client):
            with pytest.raises(ValueError):
                await extract_syllabus("x", today=date(2025, 12, 29))


@pytest.mark.asyncio
async def test_extract_syllabus_falls_back_to_legacy_on_failure() -> None:
    from datetime import date

    from app.services.llm import extract_syllabus

    legacy = [
        ParsedEvent(
            title="Midterm", due_date=datetime(2026, 2, 26, 10, 0), event_type="exam"
        )
    ]
    with (
        patch(
            "app.services.llm.transcribe_syllabus",
            new_callable=AsyncMock,
            side_effect=ValueError("bad schema"),
        ),
        patch(
            "app.services.llm.extract_events",
            new_callable=AsyncMock,
            return_value=legacy,
        ),
    ):
        outcome = await extract_syllabus("text", today=date(2025, 12, 29))

    assert outcome.events == legacy
    assert outcome.term_context is None
    assert outcome.extraction is None
