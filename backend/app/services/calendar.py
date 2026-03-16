"""Google Calendar API integration and .ics file generation."""

from app.models.schemas import ParsedEvent


async def create_ics(events: list[ParsedEvent]) -> str:
    """Generate an .ics file string from parsed events."""
    # TODO: build iCalendar format string
    raise NotImplementedError("ICS generation not yet implemented")


async def export_to_google_calendar(events: list[ParsedEvent], token: str):
    """Push events to Google Calendar via API."""
    # TODO: authenticate with token, create events
    raise NotImplementedError("Google Calendar export not yet implemented")
