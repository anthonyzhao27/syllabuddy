"""Outlook calendar export via deep links."""

from datetime import timedelta
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from app.models.schemas import ParsedEvent


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


def _timed_event_end(event: ParsedEvent, start) -> timedelta:
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


def generate_outlook_deep_link(event: ParsedEvent, timezone_name: str) -> str:
    """Generate Outlook.com deep link for a single event."""
    base_url = "https://outlook.office.com/calendar/0/deeplink/compose"
    export_tz = _get_timezone(timezone_name)
    resolved_tz = _resolved_timezone_name(export_tz, timezone_name)

    summary = _build_summary(event)

    if _is_all_day(event):
        start_dt = event.due_date.replace(hour=0, minute=0, second=0)
        end_dt = start_dt + timedelta(days=1)
        all_day = "true"
    else:
        start_dt = event.due_date.replace(tzinfo=export_tz)
        end_dt = _timed_event_end(event, start_dt)
        all_day = "false"

    params = {
        "subject": summary,
        "body": event.description or "",
        "startdt": start_dt.isoformat(timespec="seconds"),
        "enddt": end_dt.isoformat(timespec="seconds"),
        "allday": all_day,
        "path": "/calendar/action/compose",
        "rru": "addevent",
    }

    if not _is_all_day(event):
        params["timezone"] = resolved_tz

    return f"{base_url}?{urlencode(params)}"
