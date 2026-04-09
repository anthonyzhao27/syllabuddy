from datetime import datetime, timezone
from typing import cast

from app.models.db import get_authenticated_client
from app.models.schemas import ParsedEvent

Row = dict[str, object]


def _rows(result: object) -> list[Row]:
    data = getattr(result, "data", None)
    if not data:
        return []
    return cast(list[Row], data)


async def create_syllabus(
    access_token: str,
    user_id: str,
    name: str,
    source_type: str,
    course_code: str | None = None,
    original_filename: str | None = None,
    storage_paths: list[str] | None = None,
    total_file_size_bytes: int | None = None,
    tz: str | None = None,
) -> Row:
    data: Row = {
        "user_id": user_id,
        "name": name,
        "source_type": source_type,
        "course_code": course_code,
        "original_filename": original_filename,
        "storage_paths": storage_paths or [],
        "total_file_size_bytes": total_file_size_bytes,
        "parsed_at": datetime.now(timezone.utc).isoformat(),
        "timezone": tz,
    }
    rows = _rows(
        get_authenticated_client(access_token).table("syllabi").insert(data).execute()
    )
    if not rows:
        raise RuntimeError("Failed to create syllabus")
    return rows[0]


async def get_syllabus(access_token: str, syllabus_id: str) -> Row | None:
    rows = _rows(
        get_authenticated_client(access_token)
        .table("syllabi")
        .select("*")
        .eq("id", syllabus_id)
        .execute()
    )
    return rows[0] if rows else None


async def list_syllabi(access_token: str, limit: int = 50) -> list[Row]:
    return _rows(
        get_authenticated_client(access_token)
        .table("syllabi")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )


async def delete_syllabus(access_token: str, syllabus_id: str) -> bool:
    rows = _rows(
        get_authenticated_client(access_token)
        .table("syllabi")
        .delete()
        .eq("id", syllabus_id)
        .execute()
    )
    return bool(rows)


async def save_events(
    access_token: str,
    syllabus_id: str,
    user_id: str,
    events: list[ParsedEvent],
) -> list[Row]:
    if not events:
        return []

    event_records: list[Row] = [
        {
            "syllabus_id": syllabus_id,
            "user_id": user_id,
            "title": event.title,
            "due_date": event.due_date.isoformat(),
            "course": event.course,
            "event_type": event.event_type.value,
            "description": event.description,
            "time_specified": event.time_specified,
            "duration_minutes": event.duration_minutes,
        }
        for event in events
    ]

    return _rows(
        get_authenticated_client(access_token)
        .table("events")
        .insert(event_records)
        .execute()
    )


async def get_events_for_syllabus(access_token: str, syllabus_id: str) -> list[Row]:
    return _rows(
        get_authenticated_client(access_token)
        .table("events")
        .select("*")
        .eq("syllabus_id", syllabus_id)
        .eq("is_deleted", False)
        .order("due_date")
        .execute()
    )


async def get_event_counts_for_syllabi(
    access_token: str,
    syllabus_ids: list[str],
) -> dict[str, int]:
    if not syllabus_ids:
        return {}

    rows = _rows(
        get_authenticated_client(access_token)
        .table("events")
        .select("syllabus_id")
        .in_("syllabus_id", syllabus_ids)
        .eq("is_deleted", False)
        .execute()
    )

    counts: dict[str, int] = {}
    for row in rows:
        syllabus_id = row.get("syllabus_id")
        if isinstance(syllabus_id, str):
            counts[syllabus_id] = counts.get(syllabus_id, 0) + 1
    return counts


async def get_event(access_token: str, event_id: str, syllabus_id: str) -> Row | None:
    rows = _rows(
        get_authenticated_client(access_token)
        .table("events")
        .select("*")
        .eq("id", event_id)
        .eq("syllabus_id", syllabus_id)
        .eq("is_deleted", False)
        .execute()
    )
    return rows[0] if rows else None


async def update_event(
    access_token: str,
    event_id: str,
    syllabus_id: str,
    updates: dict[str, object],
) -> Row | None:
    payload = {
        **updates,
        "is_edited": True,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    rows = _rows(
        get_authenticated_client(access_token)
        .table("events")
        .update(payload)
        .eq("id", event_id)
        .eq("syllabus_id", syllabus_id)
        .eq("is_deleted", False)
        .execute()
    )
    return rows[0] if rows else None


async def soft_delete_event(access_token: str, event_id: str, syllabus_id: str) -> bool:
    rows = _rows(
        get_authenticated_client(access_token)
        .table("events")
        .update(
            {
                "is_deleted": True,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .eq("id", event_id)
        .eq("syllabus_id", syllabus_id)
        .execute()
    )
    return bool(rows)


async def update_syllabus_timezone(
    access_token: str, syllabus_id: str, tz: str
) -> Row | None:
    rows = _rows(
        get_authenticated_client(access_token)
        .table("syllabi")
        .update({"timezone": tz})
        .eq("id", syllabus_id)
        .execute()
    )
    return rows[0] if rows else None
