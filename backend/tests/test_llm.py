"""Tests for LLM extraction service."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.llm import _parse_events, extract_events


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
        assert events[0].event_type == ""
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
            [
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
            ]
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
