from datetime import datetime, timezone
from typing import cast

from fastapi.concurrency import run_in_threadpool

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
    term_context: dict | None = None,
    extraction: dict | None = None,
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
        "term_context": term_context,
        "extraction": extraction,
    }

    def _create_sync() -> list[Row]:
        return _rows(
            get_authenticated_client(access_token)
            .table("syllabi")
            .insert(data)
            .execute()
        )

    rows = await run_in_threadpool(_create_sync)
    if not rows:
        raise RuntimeError("Failed to create syllabus")
    return rows[0]


async def get_syllabus(access_token: str, syllabus_id: str) -> Row | None:
    def _get_sync() -> list[Row]:
        return _rows(
            get_authenticated_client(access_token)
            .table("syllabi")
            .select("*")
            .eq("id", syllabus_id)
            .execute()
        )

    rows = await run_in_threadpool(_get_sync)
    return rows[0] if rows else None


async def list_syllabi(access_token: str, limit: int = 50) -> list[Row]:
    def _list_sync() -> list[Row]:
        return _rows(
            get_authenticated_client(access_token)
            .table("syllabi")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

    return await run_in_threadpool(_list_sync)


async def delete_syllabus(access_token: str, syllabus_id: str) -> bool:
    def _delete_sync() -> list[Row]:
        return _rows(
            get_authenticated_client(access_token)
            .table("syllabi")
            .delete()
            .eq("id", syllabus_id)
            .execute()
        )

    rows = await run_in_threadpool(_delete_sync)
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
            "date_confidence": event.date_confidence,
            "date_source": event.date_source,
            "source_key": event.source_key,
        }
        for event in events
    ]

    def _save_sync() -> list[Row]:
        return _rows(
            get_authenticated_client(access_token)
            .table("events")
            .insert(event_records)
            .execute()
        )

    return await run_in_threadpool(_save_sync)


async def get_events_for_syllabus(access_token: str, syllabus_id: str) -> list[Row]:
    def _get_events_sync() -> list[Row]:
        return _rows(
            get_authenticated_client(access_token)
            .table("events")
            .select("*")
            .eq("syllabus_id", syllabus_id)
            .eq("is_deleted", False)
            .order("due_date")
            .execute()
        )

    return await run_in_threadpool(_get_events_sync)


async def get_deleted_events(access_token: str, syllabus_id: str) -> list[Row]:
    """Events the user deleted (soft-deleted rows)."""

    def _get_sync() -> list[Row]:
        return _rows(
            get_authenticated_client(access_token)
            .table("events")
            .select("title, source_key")
            .eq("syllabus_id", syllabus_id)
            .eq("is_deleted", True)
            .execute()
        )

    return await run_in_threadpool(_get_sync)


async def get_event_counts_for_syllabi(
    access_token: str,
    syllabus_ids: list[str],
) -> dict[str, int]:
    if not syllabus_ids:
        return {}

    def _counts_sync() -> list[Row]:
        return _rows(
            get_authenticated_client(access_token)
            .table("events")
            .select("syllabus_id")
            .in_("syllabus_id", syllabus_ids)
            .eq("is_deleted", False)
            .execute()
        )

    rows = await run_in_threadpool(_counts_sync)

    counts: dict[str, int] = {}
    for row in rows:
        syllabus_id = row.get("syllabus_id")
        if isinstance(syllabus_id, str):
            counts[syllabus_id] = counts.get(syllabus_id, 0) + 1
    return counts


async def get_event(access_token: str, event_id: str, syllabus_id: str) -> Row | None:
    def _get_event_sync() -> list[Row]:
        return _rows(
            get_authenticated_client(access_token)
            .table("events")
            .select("*")
            .eq("id", event_id)
            .eq("syllabus_id", syllabus_id)
            .eq("is_deleted", False)
            .execute()
        )

    rows = await run_in_threadpool(_get_event_sync)
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

    def _update_sync() -> list[Row]:
        return _rows(
            get_authenticated_client(access_token)
            .table("events")
            .update(payload)
            .eq("id", event_id)
            .eq("syllabus_id", syllabus_id)
            .eq("is_deleted", False)
            .execute()
        )

    rows = await run_in_threadpool(_update_sync)
    return rows[0] if rows else None


async def soft_delete_event(access_token: str, event_id: str, syllabus_id: str) -> bool:
    def _soft_delete_sync() -> list[Row]:
        return _rows(
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

    rows = await run_in_threadpool(_soft_delete_sync)
    return bool(rows)


async def update_syllabus_timezone(
    access_token: str, syllabus_id: str, tz: str
) -> Row | None:
    def _update_tz_sync() -> list[Row]:
        return _rows(
            get_authenticated_client(access_token)
            .table("syllabi")
            .update({"timezone": tz})
            .eq("id", syllabus_id)
            .execute()
        )

    rows = await run_in_threadpool(_update_tz_sync)
    return rows[0] if rows else None


async def update_syllabus_term_context(
    access_token: str, syllabus_id: str, term_context: dict
) -> Row | None:
    def _update_sync() -> list[Row]:
        return _rows(
            get_authenticated_client(access_token)
            .table("syllabi")
            .update({"term_context": term_context})
            .eq("id", syllabus_id)
            .execute()
        )

    rows = await run_in_threadpool(_update_sync)
    return rows[0] if rows else None


async def delete_events(
    access_token: str, syllabus_id: str, event_ids: list[str]
) -> None:
    """Hard-delete rows superseded by a re-date.

    Soft delete is reserved for user deletions: re-dating uses the titles of
    soft-deleted events to keep user-deleted items from coming back.
    """
    if not event_ids:
        return

    def _delete_sync() -> list[Row]:
        return _rows(
            get_authenticated_client(access_token)
            .table("events")
            .delete()
            .eq("syllabus_id", syllabus_id)
            .in_("id", event_ids)
            .execute()
        )

    await run_in_threadpool(_delete_sync)
