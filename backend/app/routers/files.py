import mimetypes
from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.middleware.auth import AuthenticatedUser, get_current_user
from app.models.schemas import (
    DeleteResponse,
    EventResponse,
    EventUpdateRequest,
    SyllabusDetailResponse,
    SyllabusListResponse,
    SyllabusResponse,
)
from app.services import storage as storage_service
from app.services import syllabi as syllabi_service

router = APIRouter()


def _require_str(row: dict[str, object], key: str) -> str:
    value = row.get(key)
    if isinstance(value, str):
        return value
    raise HTTPException(status_code=500, detail="Unexpected database response")


def _optional_str(row: dict[str, object], key: str) -> str | None:
    value = row.get(key)
    return value if isinstance(value, str) else None


def _optional_int(row: dict[str, object], key: str) -> int | None:
    value = row.get(key)
    return value if isinstance(value, int) else None


def _require_bool(row: dict[str, object], key: str) -> bool:
    value = row.get(key)
    if isinstance(value, bool):
        return value
    raise HTTPException(status_code=500, detail="Unexpected database response")


def _syllabus_response(syllabus: dict[str, object], event_count: int) -> SyllabusResponse:
    return SyllabusResponse(
        id=_require_str(syllabus, "id"),
        name=_require_str(syllabus, "name"),
        course_code=_optional_str(syllabus, "course_code"),
        source_type=_require_str(syllabus, "source_type"),
        original_filename=_optional_str(syllabus, "original_filename"),
        created_at=_require_str(syllabus, "created_at"),
        event_count=event_count,
    )


def _event_response(event: dict[str, object]) -> EventResponse:
    return EventResponse(
        id=_require_str(event, "id"),
        title=_require_str(event, "title"),
        due_date=_require_str(event, "due_date"),
        course=_require_str(event, "course"),
        event_type=_require_str(event, "event_type"),
        description=_require_str(event, "description"),
        time_specified=_require_bool(event, "time_specified"),
        duration_minutes=_optional_int(event, "duration_minutes"),
        is_edited=_require_bool(event, "is_edited"),
    )


def _normalize_due_date_update(
    due_date_value: date | datetime,
    explicit_time_specified: bool | None,
    existing_event: dict[str, object],
) -> tuple[str, bool]:
    if isinstance(due_date_value, datetime):
        if explicit_time_specified is False and due_date_value.timetz().replace(
            tzinfo=None
        ) != time(23, 59):
            raise HTTPException(
                status_code=422,
                detail="time_specified=false requires a date-only value or a 23:59 datetime",
            )
        return due_date_value.isoformat(), (
            explicit_time_specified if explicit_time_specified is not None else True
        )

    if explicit_time_specified is True:
        raise HTTPException(
            status_code=422,
            detail="time_specified=true requires a full datetime value for due_date",
        )

    if explicit_time_specified is False or not _require_bool(existing_event, "time_specified"):
        return datetime.combine(due_date_value, time(23, 59)).isoformat(), False

    existing_due_date = datetime.fromisoformat(_require_str(existing_event, "due_date"))
    return datetime.combine(due_date_value, existing_due_date.timetz()).isoformat(), True


@router.get("/", response_model=SyllabusListResponse)
async def list_user_syllabi(
    user: AuthenticatedUser = Depends(get_current_user),
) -> SyllabusListResponse:
    syllabi = await syllabi_service.list_syllabi(user.access_token)
    counts = await syllabi_service.get_event_counts_for_syllabi(
        user.access_token,
        [_require_str(syllabus, "id") for syllabus in syllabi],
    )
    return SyllabusListResponse(
        syllabi=[
            _syllabus_response(
                syllabus,
                counts.get(_require_str(syllabus, "id"), 0),
            )
            for syllabus in syllabi
        ]
    )


@router.get("/{syllabus_id}", response_model=SyllabusDetailResponse)
async def get_syllabus_detail(
    syllabus_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
) -> SyllabusDetailResponse:
    syllabus = await syllabi_service.get_syllabus(user.access_token, syllabus_id)
    if syllabus is None:
        raise HTTPException(status_code=404, detail="Syllabus not found")

    events = await syllabi_service.get_events_for_syllabus(user.access_token, syllabus_id)
    return SyllabusDetailResponse(
        syllabus=_syllabus_response(syllabus, len(events)),
        events=[_event_response(event) for event in events],
    )


@router.delete("/{syllabus_id}", response_model=DeleteResponse)
async def delete_syllabus(
    syllabus_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
) -> DeleteResponse:
    syllabus = await syllabi_service.get_syllabus(user.access_token, syllabus_id)
    if syllabus is None:
        raise HTTPException(status_code=404, detail="Syllabus not found")

    storage_paths_value = syllabus.get("storage_paths")
    storage_paths = (
        [path for path in storage_paths_value if isinstance(path, str)]
        if isinstance(storage_paths_value, list)
        else []
    )

    deleted = await syllabi_service.delete_syllabus(user.access_token, syllabus_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Syllabus not found")

    for path in storage_paths:
        await storage_service.delete_file_best_effort(path, user.access_token)

    return DeleteResponse(message="Syllabus deleted")


@router.get("/{syllabus_id}/download")
async def download_original_file(
    syllabus_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
) -> Response:
    syllabus = await syllabi_service.get_syllabus(user.access_token, syllabus_id)
    if syllabus is None:
        raise HTTPException(status_code=404, detail="Syllabus not found")

    storage_paths_value = syllabus.get("storage_paths")
    storage_paths = (
        [path for path in storage_paths_value if isinstance(path, str)]
        if isinstance(storage_paths_value, list)
        else []
    )
    if not storage_paths:
        raise HTTPException(status_code=404, detail="No files stored for this syllabus")

    if len(storage_paths) == 1:
        filename = _optional_str(syllabus, "original_filename") or storage_paths[0].split("/")[-1]
        return Response(
            content=await storage_service.download_file(storage_paths[0], user.access_token),
            media_type=mimetypes.guess_type(filename)[0] or "application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    filename = f'{_require_str(syllabus, "name")}.zip'
    return Response(
        content=await storage_service.download_files_as_zip(
            storage_paths,
            user.access_token,
        ),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.patch("/{syllabus_id}/events/{event_id}", response_model=EventResponse)
async def update_event(
    syllabus_id: str,
    event_id: str,
    updates: EventUpdateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> EventResponse:
    existing_event = await syllabi_service.get_event(
        user.access_token,
        event_id,
        syllabus_id,
    )
    if existing_event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found or does not belong to this syllabus",
        )

    update_data = dict(updates.model_dump(exclude_none=True))
    if "due_date" in update_data:
        due_date_value = updates.due_date
        if due_date_value is None:
            raise HTTPException(status_code=400, detail="No updates provided")
        due_date, time_specified = _normalize_due_date_update(
            due_date_value,
            updates.time_specified,
            existing_event,
        )
        update_data["due_date"] = due_date
        update_data["time_specified"] = time_specified

    if updates.event_type is not None:
        update_data["event_type"] = updates.event_type.value

    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")

    updated = await syllabi_service.update_event(
        user.access_token,
        event_id,
        syllabus_id,
        update_data,
    )
    if updated is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found or does not belong to this syllabus",
        )

    return _event_response(updated)


@router.delete("/{syllabus_id}/events/{event_id}", response_model=DeleteResponse)
async def delete_event(
    syllabus_id: str,
    event_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
) -> DeleteResponse:
    deleted = await syllabi_service.soft_delete_event(
        user.access_token,
        event_id,
        syllabus_id,
    )
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Event not found or does not belong to this syllabus",
        )

    return DeleteResponse(message="Event deleted")
