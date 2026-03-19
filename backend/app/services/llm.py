"""OpenAI structured extraction for syllabus parsing."""

import json
import logging

from openai import AsyncOpenAI

from app.config import settings
from app.models.schemas import ParsedEvent
from app.utils.prompts import EXTRACTION_PROMPT

logger = logging.getLogger(__name__)


async def extract_events(text: str) -> list[ParsedEvent]:
    """Send syllabus text to OpenAI and return structured events."""
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": EXTRACTION_PROMPT},
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
    )

    raw = response.choices[0].message.content or ""
    return _parse_events(raw)


def _parse_events(raw: str) -> list[ParsedEvent]:
    """Parse raw JSON string from LLM into validated ParsedEvent list.

    Handles two shapes:
    - A JSON array: [{ ... }, { ... }]
    - A JSON object with an array value: {"events": [{ ... }]}
    """
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
            events.append(ParsedEvent(**item))
        except Exception as e:
            logger.warning("Skipping malformed event %r: %s", item, e)
            continue

    return events
