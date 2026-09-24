import json
import logging
import mimetypes
from collections import Counter
from datetime import date, datetime, time

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import Response

from app.middleware.auth import AuthenticatedUser, get_current_user
from app.middleware.limiter import limiter
from app.models.schemas import (
    DeleteResponse,
    EventResponse,
    EventUpdateRequest,
    LLMSyllabus,
    ParsedEvent,
    SaveResponse,
    SyllabusDetailResponse,
    SyllabusListResponse,
    SyllabusResolveRequest,
    SyllabusResponse,
    SyllabusUpdateRequest,
    TermContext,
)
from app.services import storage as storage_service
from app.services import syllabi as syllabi_service
from app.services.extraction import classify_upload
from app.services.llm import resolve_extraction

# The stored transcription is echoed back from /parse; cap what we accept.
MAX_EXTRACTION_JSON_BYTES = 512 * 1024

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=SaveResponse)
@limiter.limit("20/hour;60/day")
async def save_syllabus(
    request: Request,
    files: list[UploadFile] = File(default=[]),
    events_json: str = Form(...),
    syllabus_name: str | None = Form(default=None),
    timezone: str | None = Form(default=None),
    term_context_json: str | None = Form(default=None),
    extraction_json: str | None = Form(default=None),
    user: AuthenticatedUser = Depends(get_current_user),
) -> SaveResponse:
    """Save parsed syllabus events and files to storage.

    This endpoint should be called after reviewing the parsed events from /parse.
    """
    if not files or not files[0].filename:
        raise HTTPException(status_code=400, detail="Please upload a file.")

    try:
        events_data = json.loads(events_json)
        events = [ParsedEvent(**e) for e in events_data]
    except (json.JSONDecodeError, TypeError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid events JSON: {e}")

    term_context, extraction = _parse_term_payload(term_context_json, extraction_json)

    first_kind = await classify_upload(files[0])
    if first_kind == "image":
        source_type = "screenshots"
        original_filename = None
    else:
        source_type = "file"
        original_filename = files[0].filename

    course_codes = [event.course.strip() for event in events if event.course.strip()]
    course_code = Counter(course_codes).most_common(1)[0][0] if course_codes else None

    storage_paths: list[str] = []
    syllabus: dict[str, object] | None = None

    try:
        upload_result = await storage_service.upload_files(
            files,
            user.id,
            user.access_token,
        )
        storage_paths_value = upload_result["paths"]
        if not isinstance(storage_paths_value, list):
            raise RuntimeError("Invalid upload response")
        storage_paths = [path for path in storage_paths_value if isinstance(path, str)]
        total_size = upload_result["total_size"]
        if not isinstance(total_size, int):
            raise RuntimeError("Invalid upload response")

        syllabus = await syllabi_service.create_syllabus(
            user.access_token,
            user.id,
            name=syllabus_name
            or original_filename
            or f"Syllabus - {course_code or 'Unknown'}",
            source_type=source_type,
            course_code=course_code,
            original_filename=original_filename,
            storage_paths=storage_paths,
            total_file_size_bytes=total_size,
            tz=timezone,
            term_context=term_context,
            extraction=extraction,
        )
        syllabus_id = syllabus.get("id")
        if not isinstance(syllabus_id, str):
            raise RuntimeError("Invalid syllabus response")

        await syllabi_service.save_events(
            user.access_token,
            syllabus_id,
            user.id,
            events,
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to save syllabus")
        for path in storage_paths:
            await storage_service.delete_file_best_effort(path, user.access_token)
        if syllabus is not None:
            syllabus_id = syllabus.get("id")
            if isinstance(syllabus_id, str):
                try:
                    await syllabi_service.delete_syllabus(
                        user.access_token, syllabus_id
                    )
                except Exception:
                    pass
        raise HTTPException(
            status_code=503,
            detail="Failed to save syllabus. Please try again.",
        )

    return SaveResponse(syllabus_id=syllabus_id)


def _parse_term_payload(
    term_context_json: str | None, extraction_json: str | None
) -> tuple[dict | None, dict | None]:
    """Validate the optional term anchor + transcription sent back from /parse.

    Both are optional (older clients, screenshot flows); a bad payload is
    dropped rather than failing the save, since the events are what matter.
    """
    if not term_context_json or not extraction_json:
        return None, None
    if len(extraction_json) > MAX_EXTRACTION_JSON_BYTES:
        logger.warning("Dropping oversized extraction payload on save")
        return None, None
    try:
        term_context = TermContext.model_validate_json(term_context_json)
        extraction = LLMSyllabus.model_validate_json(extraction_json)
    except Exception:
        logger.warning("Dropping invalid term context / extraction on save")
        return None, None
    return term_context.model_dump(mode="json"), extraction.model_dump(mode="json")


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


def _term_context(syllabus: dict[str, object]) -> TermContext | None:
    raw = syllabus.get("term_context")
    if not isinstance(raw, dict):
        return None
    try:
        return TermContext.model_validate(raw)
    except Exception:
        return None


def _syllabus_response(
    syllabus: dict[str, object], event_count: int
) -> SyllabusResponse:
    term_context = _term_context(syllabus)
    return SyllabusResponse(
        id=_require_str(syllabus, "id"),
        name=_require_str(syllabus, "name"),
        course_code=_optional_str(syllabus, "course_code"),
        source_type=_require_str(syllabus, "source_type"),
        original_filename=_optional_str(syllabus, "original_filename"),
        created_at=_require_str(syllabus, "created_at"),
        event_count=event_count,
        timezone=_optional_str(syllabus, "timezone"),
        term_context=term_context,
        can_redate=term_context is not None
        and isinstance(syllabus.get("extraction"), dict),
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
        date_confidence=_optional_str(event, "date_confidence"),
        date_source=_optional_str(event, "date_source") or "",
        source_key=_optional_str(event, "source_key") or "",
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
                detail=(
                    "time_specified=false requires a date-only value or a "
                    "23:59 datetime"
                ),
            )
        return due_date_value.isoformat(), (
            explicit_time_specified if explicit_time_specified is not None else True
        )

    if explicit_time_specified is True:
        raise HTTPException(
            status_code=422,
            detail="time_specified=true requires a full datetime value for due_date",
        )

    if explicit_time_specified is False or not _require_bool(
        existing_event, "time_specified"
    ):
        return datetime.combine(due_date_value, time(23, 59)).isoformat(), False

    existing_due_date = datetime.fromisoformat(_require_str(existing_event, "due_date"))
    return (
        datetime.combine(due_date_value, existing_due_date.timetz()).isoformat(),
        True,
    )


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

    events = await syllabi_service.get_events_for_syllabus(
        user.access_token, syllabus_id
    )
    return SyllabusDetailResponse(
        syllabus=_syllabus_response(syllabus, len(events)),
        events=[_event_response(event) for event in events],
    )


@router.patch("/{syllabus_id}", response_model=SyllabusResponse)
@limiter.limit("120/hour")
async def update_syllabus(
    request: Request,
    syllabus_id: str,
    updates: SyllabusUpdateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> SyllabusResponse:
    syllabus = await syllabi_service.get_syllabus(user.access_token, syllabus_id)
    if syllabus is None:
        raise HTTPException(status_code=404, detail="Syllabus not found")

    if updates.timezone is None:
        raise HTTPException(status_code=400, detail="No updates provided")

    updated = await syllabi_service.update_syllabus_timezone(
        user.access_token, syllabus_id, updates.timezone
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Syllabus not found")

    events = await syllabi_service.get_events_for_syllabus(
        user.access_token, syllabus_id
    )
    return _syllabus_response(updated, len(events))


@router.delete("/{syllabus_id}", response_model=DeleteResponse)
@limiter.limit("120/hour")
async def delete_syllabus(
    request: Request,
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
        filename = (
            _optional_str(syllabus, "original_filename")
            or storage_paths[0].split("/")[-1]
        )
        return Response(
            content=await storage_service.download_file(
                storage_paths[0], user.access_token
            ),
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
@limiter.limit("120/hour")
async def update_event(
    request: Request,
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
        # A date the user set by hand is no longer our inference
        update_data["date_confidence"] = None
        update_data["date_source"] = ""

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


@router.post("/{syllabus_id}/resolve", response_model=SyllabusDetailResponse)
@limiter.limit("60/hour")
async def resolve_saved_syllabus(
    request: Request,
    syllabus_id: str,
    body: SyllabusResolveRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> SyllabusDetailResponse:
    """Re-date a saved syllabus with a corrected term anchor. No LLM call.

    Events the user edited are kept as-is; every other event is replaced by
    the re-resolved set, skipping items the user edited or deleted (matched by
    source_key, or by title for rows saved without one) so deletions stay
    deleted and edits aren't duplicated.
    """
    syllabus = await syllabi_service.get_syllabus(user.access_token, syllabus_id)
    if syllabus is None:
        raise HTTPException(status_code=404, detail="Syllabus not found")
    raw_extraction = syllabus.get("extraction")
    if not isinstance(raw_extraction, dict):
        raise HTTPException(
            status_code=409, detail="This syllabus can't be re-dated automatically."
        )
    try:
        extraction = LLMSyllabus.model_validate(raw_extraction)
    except Exception:
        raise HTTPException(
            status_code=409, detail="This syllabus can't be re-dated automatically."
        )

    parsed_at = _optional_str(syllabus, "parsed_at") or _require_str(
        syllabus, "created_at"
    )
    upload_day = datetime.fromisoformat(parsed_at).date()
    new_events, term_context = resolve_extraction(extraction, upload_day, body.override)

    existing = await syllabi_service.get_events_for_syllabus(
        user.access_token, syllabus_id
    )
    deleted = await syllabi_service.get_deleted_events(user.access_token, syllabus_id)
    claimed = [e for e in existing if e.get("is_edited")] + deleted
    claimed_keys = {k for e in claimed if (k := _optional_str(e, "source_key"))}
    claimed_titles = {
        _norm_title(_require_str(e, "title"))
        for e in claimed
        if not _optional_str(e, "source_key")
    }
    stale_ids = [_require_str(e, "id") for e in existing if not e.get("is_edited")]
    to_insert = [
        e
        for e in new_events
        if e.source_key not in claimed_keys
        and _norm_title(e.title) not in claimed_titles
    ]

    # Insert first, then remove the superseded rows by id, so a failure
    # part-way never leaves the syllabus with no events.
    await syllabi_service.save_events(
        user.access_token, syllabus_id, user.id, to_insert
    )
    await syllabi_service.delete_events(user.access_token, syllabus_id, stale_ids)
    updated = await syllabi_service.update_syllabus_term_context(
        user.access_token, syllabus_id, term_context.model_dump(mode="json")
    )

    events = await syllabi_service.get_events_for_syllabus(
        user.access_token, syllabus_id
    )
    return SyllabusDetailResponse(
        syllabus=_syllabus_response(updated or syllabus, len(events)),
        events=[_event_response(event) for event in events],
    )


def _norm_title(title: str) -> str:
    return " ".join(title.lower().split())


@router.delete("/{syllabus_id}/events/{event_id}", response_model=DeleteResponse)
@limiter.limit("120/hour")
async def delete_event(
    request: Request,
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
