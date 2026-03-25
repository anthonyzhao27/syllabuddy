"""Google Calendar API integration."""

import logging
from datetime import timedelta
from typing import Any
from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.models.schemas import ParsedEvent

logger = logging.getLogger(__name__)


def _build_summary(event: ParsedEvent) -> str:
    """Build event summary with optional course prefix."""
    if event.course:
        return f"[{event.course}] {event.title}"
    return event.title


def _is_all_day(event: ParsedEvent) -> bool:
    """Export inferred date-only events as all-day; explicit times stay timed."""
    return not event.time_specified


def _get_timezone(timezone_name: str) -> ZoneInfo:
    """Validate and return a ZoneInfo object, falling back to UTC on invalid input."""
    try:
        return ZoneInfo(timezone_name)
    except (KeyError, ValueError):
        return ZoneInfo("UTC")


def _resolved_timezone_name(export_tz: ZoneInfo, requested: str) -> str:
    """Return the canonical timezone name actually used by the exporter."""
    return getattr(export_tz, "key", requested or "UTC")


def _timed_event_end(event: ParsedEvent, start):
    """Use a short marker window for deadline-like events, 1 hour otherwise."""
    deadline_like = {
        "assignment",
        "project",
        "milestone",
        "deadline",
        "lab",
        "discussion",
        "other",
    }

    if str(event.event_type) in deadline_like:
        return start + timedelta(minutes=5)

    return start + timedelta(hours=1)


def _build_calendar_event(event: ParsedEvent, timezone: str) -> dict[str, Any]:
    """Convert ParsedEvent to Google Calendar event format."""
    summary = _build_summary(event)
    export_tz = _get_timezone(timezone)
    resolved_tz = _resolved_timezone_name(export_tz, timezone)

    if _is_all_day(event):
        start_date = event.due_date.strftime("%Y-%m-%d")
        end_date = (event.due_date + timedelta(days=1)).strftime("%Y-%m-%d")
        return {
            "summary": summary,
            "description": event.description or "",
            "start": {"date": start_date},
            "end": {"date": end_date},
        }
    else:
        local_start = event.due_date.replace(tzinfo=export_tz)
        local_end = _timed_event_end(event, local_start)
        return {
            "summary": summary,
            "description": event.description or "",
            "start": {"dateTime": local_start.isoformat(), "timeZone": resolved_tz},
            "end": {"dateTime": local_end.isoformat(), "timeZone": resolved_tz},
        }


def export_to_google_calendar_sync(
    events: list[ParsedEvent],
    access_token: str,
    calendar_id: str = "primary",
    timezone: str = "UTC",
) -> dict[str, Any]:
    """Synchronous Google Calendar export."""
    credentials = Credentials(token=access_token)
    service = build("calendar", "v3", credentials=credentials)

    created: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []

    for event in events:
        try:
            calendar_event = _build_calendar_event(event, timezone)
            result = (
                service.events()
                .insert(calendarId=calendar_id, body=calendar_event)
                .execute()
            )
            created.append(
                {
                    "title": event.title,
                    "id": result.get("id", ""),
                    "link": result.get("htmlLink", ""),
                }
            )
            logger.info(f"Created Google Calendar event: {event.title}")
        except HttpError as e:
            logger.error(f"Failed to create event '{event.title}': {e}")
            errors.append(
                {
                    "title": event.title,
                    "error": str(e),
                }
            )

    return {
        "created_count": len(created),
        "created": created,
        "errors": errors,
    }
