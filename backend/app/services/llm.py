"""OpenAI structured extraction for syllabus parsing."""

from app.models.schemas import ParsedEvent
from app.utils.prompts import EXTRACTION_PROMPT


async def extract_events(text: str) -> list[ParsedEvent]:
    """Send syllabus text to OpenAI and return structured events."""
    # TODO: call OpenAI API with EXTRACTION_PROMPT + text
    # TODO: parse response into ParsedEvent list
    raise NotImplementedError("LLM extraction not yet implemented")
