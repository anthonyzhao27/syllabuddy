"""RFC 5545 compliant iCalendar (.ics) file generation."""

import hashlib
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.models.schemas import ParsedEvent


def _escape_ics(text: str) -> str:
    """Escape special characters per RFC 5545."""
    if not text:
        return ""
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def _generate_uid(event: ParsedEvent) -> str:
    """Generate a unique identifier for an event."""
    content = f"{event.title}-{event.due_date.isoformat()}-{event.course}"
    hash_digest = hashlib.md5(content.encode()).hexdigest()[:16]
    return f"{hash_digest}@syllabusparser.app"


def _format_utc_datetime(dt: datetime) -> str:
    """Format UTC datetime for iCalendar (YYYYMMDDTHHmmssZ)."""
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _fold_ics_line(line: str, limit: int = 75) -> list[str]:
    """Fold a content line per RFC 5545 using continuation lines."""
    if len(line.encode("utf-8")) <= limit:
        return [line]

    folded: list[str] = []
    remaining = line

    while remaining:
        chunk = ""
        for char in remaining:
            candidate = chunk + char
            if len(candidate.encode("utf-8")) > limit and chunk:
                break
            chunk = candidate

        folded.append(chunk if not folded else f" {chunk}")
        remaining = remaining[len(chunk) :]

    return folded


def _get_timezone(timezone_name: str) -> ZoneInfo:
    """Validate and return a ZoneInfo object, falling back to UTC on invalid input."""
    try:
        return ZoneInfo(timezone_name)
    except (KeyError, ValueError):
        return ZoneInfo("UTC")


def _is_all_day(event: ParsedEvent) -> bool:
    """Export inferred date-only events as all-day; explicit times stay timed."""
    return not event.time_specified


def _build_summary(event: ParsedEvent) -> str:
    """Build event summary with optional course prefix."""
    if event.course:
        return f"[{event.course}] {event.title}"
    return event.title


def _timed_event_end(event: ParsedEvent, start: datetime) -> datetime:
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


def create_ics(
    events: list[ParsedEvent],
    timezone_name: str,
    calendar_name: str = "Syllabus Events",
) -> str:
    """Generate RFC 5545 compliant iCalendar content."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Syllabus Parser//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape_ics(calendar_name)}",
    ]

    export_tz = _get_timezone(timezone_name)
    timestamp = _format_utc_datetime(datetime.now(timezone.utc))

    for event in events:
        uid = _generate_uid(event)
        summary = _escape_ics(_build_summary(event))
        description = _escape_ics(event.description)
        is_all_day = _is_all_day(event)

        lines.extend(_fold_ics_line("BEGIN:VEVENT"))
        lines.extend(_fold_ics_line(f"UID:{uid}"))
        lines.extend(_fold_ics_line(f"DTSTAMP:{timestamp}"))

        if is_all_day:
            start_date = event.due_date.date()
            end_date = start_date + timedelta(days=1)
            lines.extend(
                _fold_ics_line(f"DTSTART;VALUE=DATE:{start_date.strftime('%Y%m%d')}")
            )
            lines.extend(
                _fold_ics_line(f"DTEND;VALUE=DATE:{end_date.strftime('%Y%m%d')}")
            )
        else:
            local_start = event.due_date.replace(tzinfo=export_tz)
            local_end = _timed_event_end(event, local_start)
            start_str = _format_utc_datetime(local_start)
            end_str = _format_utc_datetime(local_end)
            lines.extend(_fold_ics_line(f"DTSTART:{start_str}"))
            lines.extend(_fold_ics_line(f"DTEND:{end_str}"))

        lines.extend(_fold_ics_line(f"SUMMARY:{summary}"))

        if description:
            lines.extend(_fold_ics_line(f"DESCRIPTION:{description}"))

        if event.event_type:
            lines.extend(_fold_ics_line(f"CATEGORIES:{str(event.event_type).upper()}"))

        lines.extend(_fold_ics_line("END:VEVENT"))

    lines.extend(_fold_ics_line("END:VCALENDAR"))

    return "\r\n".join(lines)
