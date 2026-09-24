"""OpenAI structured extraction for syllabus parsing."""

import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import date
from datetime import time as dt_time

from openai import AsyncOpenAI

from app.config import settings
from openai.lib._pydantic import to_strict_json_schema

from app.models.schemas import (
    EventType,
    LLMExtractionResult,
    LLMSyllabus,
    ParsedEvent,
    RecurringEvent,
    TermContext,
    TermOverride,
)
from app.services import date_resolver
from app.services.recurrence import expand_all_recurrences
from app.utils.prompts import (
    EXTRACTION_PROMPT,
    SYLLABUS_PROMPT,
    SYLLABUS_USER_TEMPLATE,
)

logger = logging.getLogger(__name__)

# Explicit timeout (seconds) for OpenAI calls. The SDK default is 600s, which
# lets a single hung request tie up a worker for ten minutes. 60s is generous
# for a JSON extraction completion while still bounding worker exposure.
OPENAI_TIMEOUT_SECONDS = 60.0

# Hard per-request cap on the syllabus text we send to OpenAI, as a cost guard.
# Rough estimate: ~4 chars/token for English (OpenAI's own rule of thumb), so
# 240_000 chars ~= 60k input tokens. The configured gpt-4o-mini model has a
# 128k context window, so this leaves ample room for the system prompt + the
# JSON completion while capping the worst-case input bill from a maliciously
# or accidentally huge upload.
MAX_PROMPT_CHARS = 240_000

DURATION_PATTERN = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*(hours?|hrs?|minutes?|mins?|m|h)\s*$",
    re.IGNORECASE,
)

DEFAULT_DURATIONS: dict[EventType, int] = {
    EventType.EXAM: 120,
    EventType.QUIZ: 30,
    EventType.PRESENTATION: 30,
}

DEFAULT_TIMED_DURATION = 30

DEADLINE_LIKE_TYPES: set[str] = {
    "assignment",
    "project",
    "milestone",
    "deadline",
    "lab",
    "discussion",
    "other",
}


def _parse_duration(value: int | float | str | None) -> int | None:
    if value is None:
        return None

    if isinstance(value, int):
        return value if value > 0 else None

    if isinstance(value, (str, float)):
        try:
            as_int = int(float(value))
            return as_int if as_int > 0 else None
        except (ValueError, TypeError):
            pass

    if isinstance(value, str):
        match = DURATION_PATTERN.match(value.strip())
        if match:
            amount = float(match.group(1))
            unit = match.group(2).lower()

            if unit.startswith("h"):
                minutes = int(amount * 60)
            else:
                minutes = int(amount)

            return minutes if minutes > 0 else None

    return None


def _apply_smart_defaults(event: ParsedEvent) -> ParsedEvent:
    if event.duration_minutes is not None and event.duration_minutes > 0:
        return event

    if not event.time_specified:
        return event

    event_time = event.due_date.time()
    is_2359 = event_time.hour == 23 and event_time.minute == 59
    is_deadline_like = str(event.event_type) in DEADLINE_LIKE_TYPES

    if is_2359 and is_deadline_like:
        adjusted_date = event.due_date.replace(hour=23, minute=30, second=0)
        return ParsedEvent(
            title=event.title,
            due_date=adjusted_date,
            course=event.course,
            event_type=event.event_type,
            description=event.description,
            time_specified=event.time_specified,
            duration_minutes=DEFAULT_TIMED_DURATION,
        )

    duration = DEFAULT_DURATIONS.get(event.event_type, DEFAULT_TIMED_DURATION)

    return ParsedEvent(
        title=event.title,
        due_date=event.due_date,
        course=event.course,
        event_type=event.event_type,
        description=event.description,
        time_specified=event.time_specified,
        duration_minutes=duration,
    )


def _apply_all_smart_defaults(events: list[ParsedEvent]) -> list[ParsedEvent]:
    return [_apply_smart_defaults(e) for e in events]


EVENT_TYPE_SYNONYMS: dict[str, EventType] = {
    "midterm": EventType.EXAM,
    "final": EventType.EXAM,
    "test": EventType.EXAM,
    "homework": EventType.ASSIGNMENT,
    "problem_set": EventType.ASSIGNMENT,
    "hw": EventType.ASSIGNMENT,
    "checkpoint": EventType.MILESTONE,
    "due": EventType.DEADLINE,
    "submission": EventType.DEADLINE,
}


def normalize_event_type(raw: str) -> EventType:
    """Normalize LLM output to canonical EventType."""
    if not raw:
        return EventType.OTHER

    lower = raw.lower().strip()

    try:
        return EventType(lower)
    except ValueError:
        pass

    if lower in EVENT_TYPE_SYNONYMS:
        return EVENT_TYPE_SYNONYMS[lower]

    return EventType.OTHER


def _normalize_event_payload(item: dict) -> dict:
    """Normalize raw LLM event payload before Pydantic validation."""
    normalized = dict(item)
    normalized["event_type"] = normalize_event_type(normalized.get("event_type", ""))
    normalized.setdefault("time_specified", True)
    raw_duration = normalized.get("duration_minutes")
    normalized["duration_minutes"] = _parse_duration(raw_duration)
    return normalized


def _normalize_recurring_payload(item: dict) -> dict:
    """Normalize recurring event payload before Pydantic validation."""
    normalized = dict(item)
    normalized["event_type"] = normalize_event_type(normalized.get("event_type", ""))
    normalized["duration_minutes"] = _parse_duration(normalized.get("duration_minutes"))

    if "recurrence" in normalized and isinstance(normalized["recurrence"], dict):
        rec = normalized["recurrence"]

        if isinstance(rec.get("start_date"), str):
            rec["start_date"] = date.fromisoformat(rec["start_date"])
        if isinstance(rec.get("end_date"), str):
            rec["end_date"] = date.fromisoformat(rec["end_date"])

        if isinstance(rec.get("time"), str):
            rec["time"] = dt_time.fromisoformat(rec["time"])

        if isinstance(rec.get("exclusions"), list):
            parsed_exclusions: list[date] = []
            for d in rec["exclusions"]:
                try:
                    parsed_exclusions.append(
                        date.fromisoformat(d) if isinstance(d, str) else d
                    )
                except (ValueError, TypeError):
                    logger.warning("Skipping invalid exclusion date %r", d)
            rec["exclusions"] = parsed_exclusions

        if isinstance(rec.get("weekday"), str):
            rec["weekday"] = rec["weekday"].lower()

    return normalized


def _parse_extraction_result(raw: str) -> LLMExtractionResult:
    """Parse raw JSON into LLMExtractionResult with both event types."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        stripped = (
            raw.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError:
            raise ValueError(f"Could not parse LLM response as JSON: {raw[:200]}")

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object, got {type(data).__name__}")

    events: list[ParsedEvent] = []
    for item in data.get("events", []):
        try:
            normalized = _normalize_event_payload(item)
            events.append(ParsedEvent(**normalized))
        except Exception as e:
            logger.warning("Skipping malformed event %r: %s", item, e)

    recurring_events: list[RecurringEvent] = []
    for item in data.get("recurring_events", []):
        try:
            normalized = _normalize_recurring_payload(item)
            recurring_events.append(RecurringEvent(**normalized))
        except Exception as e:
            logger.warning("Skipping malformed recurring event %r: %s", item, e)

    return LLMExtractionResult(events=events, recurring_events=recurring_events)


async def extract_events(text: str) -> list[ParsedEvent]:
    """Send syllabus text to OpenAI and return structured events."""
    if len(text) > MAX_PROMPT_CHARS:
        logger.warning(
            "Syllabus text of %d chars exceeds cap, truncating to %d chars",
            len(text),
            MAX_PROMPT_CHARS,
        )
        text = text[:MAX_PROMPT_CHARS]

    client = AsyncOpenAI(
        api_key=settings.openai_api_key, timeout=OPENAI_TIMEOUT_SECONDS
    )

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": EXTRACTION_PROMPT},
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
        max_tokens=4096,
    )

    raw = response.choices[0].message.content or ""

    result = _parse_extraction_result(raw)
    expanded = expand_all_recurrences(result.recurring_events)
    all_events = result.events + expanded
    all_events = _apply_all_smart_defaults(all_events)

    return all_events


SYLLABUS_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "syllabus",
        "strict": True,
        "schema": to_strict_json_schema(LLMSyllabus),
    },
}

# Output budget for the transcription call. Long week-by-week schedules with
# source_text snippets can run several thousand tokens.
SYLLABUS_MAX_OUTPUT_TOKENS = 12_000


@dataclass
class ExtractionOutcome:
    events: list[ParsedEvent]
    # None when the structured pipeline failed and we fell back to the legacy
    # single-shot extraction (no term anchor, nothing to re-date).
    term_context: TermContext | None
    extraction: LLMSyllabus | None
    raw: str


def _completion_kwargs(model: str) -> dict:
    """Sampling params differ between classic chat models and reasoning models."""
    if model.startswith(("gpt-5", "o1", "o3", "o4")):
        return {
            "max_completion_tokens": SYLLABUS_MAX_OUTPUT_TOKENS + 8_000,
            "reasoning_effort": "low",
        }
    return {"temperature": 0.0, "max_tokens": SYLLABUS_MAX_OUTPUT_TOKENS}


async def transcribe_syllabus(
    text: str, today: date, model: str | None = None
) -> tuple[LLMSyllabus, str]:
    """Ask the LLM to transcribe the syllabus schedule into LLMSyllabus."""
    if len(text) > MAX_PROMPT_CHARS:
        logger.warning(
            "Syllabus text of %d chars exceeds cap, truncating to %d chars",
            len(text),
            MAX_PROMPT_CHARS,
        )
        text = text[:MAX_PROMPT_CHARS]
    model = model or settings.openai_model
    client = AsyncOpenAI(
        api_key=settings.openai_api_key, timeout=OPENAI_TIMEOUT_SECONDS * 3
    )
    user = SYLLABUS_USER_TEMPLATE.format(
        today=today.isoformat(), weekday=today.strftime("%A"), text=text
    )
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYLLABUS_PROMPT},
            {"role": "user", "content": user},
        ],
        response_format=SYLLABUS_RESPONSE_FORMAT,  # type: ignore[arg-type]
        **_completion_kwargs(model),
    )
    raw = response.choices[0].message.content or ""
    try:
        return LLMSyllabus.model_validate_json(raw), raw
    except Exception as e:
        raise ValueError(f"Could not parse LLM response: {raw[:200]}") from e


def _apply_defaults_keep_meta(events: list[ParsedEvent]) -> list[ParsedEvent]:
    out = []
    for e in events:
        d = _apply_smart_defaults(e)
        out.append(
            d.model_copy(
                update={
                    "date_confidence": e.date_confidence,
                    "date_source": e.date_source,
                    "source_key": e.source_key,
                }
            )
        )
    return out


def resolve_extraction(
    extraction: LLMSyllabus, today: date, override: TermOverride | None = None
) -> tuple[list[ParsedEvent], TermContext]:
    """Pure-Python re-dating of a stored transcription (no LLM call)."""
    events, ctx = date_resolver.resolve(extraction, today, override)
    return _apply_defaults_keep_meta(events), ctx


async def extract_syllabus(
    text: str,
    today: date | None = None,
    model: str | None = None,
    override: TermOverride | None = None,
) -> ExtractionOutcome:
    """Transcribe with the LLM, then resolve dates deterministically.

    If the structured call fails (schema/refusal/timeout), fall back to the
    legacy one-shot extraction so the user still gets events.
    """
    today = today or date.today()
    started = time.monotonic()
    try:
        extraction, raw = await transcribe_syllabus(text, today, model)
        extraction = date_resolver.sanitize(extraction, text)
        events, ctx = resolve_extraction(extraction, today, override)
    except Exception:
        logger.exception("Structured syllabus extraction failed; using legacy path")
        events = await extract_events(text)
        logger.info(
            "syllabus_extraction fallback=true model=%s events=%d seconds=%.1f",
            model or settings.openai_model,
            len(events),
            time.monotonic() - started,
        )
        return ExtractionOutcome(
            events=events, term_context=None, extraction=None, raw=""
        )

    confidence = {
        c: sum(e.date_confidence == c for e in events)
        for c in ("exact", "inferred", "estimated")
    }
    logger.info(
        "syllabus_extraction fallback=false model=%s events=%d exact=%d inferred=%d "
        "estimated=%d term=%s anchor=%s year=%s seconds=%.1f",
        model or settings.openai_model,
        len(events),
        confidence["exact"],
        confidence["inferred"],
        confidence["estimated"],
        ctx.term_id,
        ctx.anchor_source,
        ctx.year_source,
        time.monotonic() - started,
    )
    return ExtractionOutcome(
        events=events, term_context=ctx, extraction=extraction, raw=raw
    )


def _parse_events(raw: str) -> list[ParsedEvent]:
    """Parse raw JSON string from LLM into validated ParsedEvent list."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("LLM returned invalid JSON, attempting fence strip")
        stripped = (
            raw.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError:
            raise ValueError(f"Could not parse LLM response as JSON: {raw[:200]}")

    if isinstance(data, dict):
        if not data:
            # Empty object {} means no events found
            return []
        for v in data.values():
            if isinstance(v, list):
                data = v
                break
        else:
            raise ValueError(
                f"LLM returned a JSON object with no array field: {raw[:200]}"
            )

    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array, got {type(data).__name__}: {raw[:200]}")

    events: list[ParsedEvent] = []
    for item in data:
        try:
            normalized = _normalize_event_payload(item)
            events.append(ParsedEvent(**normalized))
        except Exception as e:
            logger.warning("Skipping malformed event %r: %s", item, e)
            continue

    return events
