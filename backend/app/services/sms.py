"""Twilio SMS reminders with AI friend-style messages."""

from app.models.schemas import ParsedEvent


async def send_reminder(event: ParsedEvent, phone_number: str):
    """Send an AI-generated friendly reminder SMS for an upcoming event."""
    # TODO: generate friendly message via LLM
    # TODO: send via Twilio
    raise NotImplementedError("SMS reminders not yet implemented")
