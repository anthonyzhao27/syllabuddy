"""Calendar export endpoints."""

import logging

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response

from app.models.schemas import (
    ExportRequest,
    GoogleExportRequest,
    GoogleExportResponse,
    IcsExportRequest,
    OutlookExportRequest,
)
from app.services.calendar_utils import (
    validate_and_get_course_code,
    get_calendar_name,
    sanitize_filename,
    MissingCourseCodeError,
    MixedCourseError,
)
from app.services.google_calendar import export_to_google_calendar_sync
from app.services.ics import create_ics

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/")
async def export_calendar(request: ExportRequest):
    """Legacy endpoint - export parsed events."""
    return {"status": "not implemented"}


@router.post("/ics")
async def export_ics(request: IcsExportRequest) -> Response:
    """Generate and return an .ics file for download."""
    if not request.events:
        raise HTTPException(status_code=400, detail="No events to export")

    try:
        course_code = validate_and_get_course_code(request.events)
        calendar_name = get_calendar_name(course_code)
    except (MissingCourseCodeError, MixedCourseError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    ics_content = create_ics(request.events, request.timezone, calendar_name)
    filename = f"{sanitize_filename(calendar_name)}.ics"

    return Response(
        content=ics_content,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/outlook")
async def export_outlook(request: OutlookExportRequest) -> Response:
    """Export events to Outlook as ICS file."""
    if not request.events:
        raise HTTPException(status_code=400, detail="No events to export")

    try:
        course_code = validate_and_get_course_code(request.events)
        calendar_name = get_calendar_name(course_code)
    except (MissingCourseCodeError, MixedCourseError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    ics_content = create_ics(request.events, request.timezone, calendar_name)
    filename = f"{sanitize_filename(calendar_name)}.ics"

    return Response(
        content=ics_content,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/google", response_model=GoogleExportResponse)
async def export_google(request: GoogleExportRequest):
    """Export events to Google Calendar using OAuth token."""
    if not request.events:
        raise HTTPException(status_code=400, detail="No events to export")

    if not request.access_token:
        raise HTTPException(status_code=400, detail="Access token required")

    try:
        result = await run_in_threadpool(
            export_to_google_calendar_sync,
            request.events,
            request.access_token,
            request.timezone,
        )
        return GoogleExportResponse(**result)
    except (MissingCourseCodeError, MixedCourseError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Google Calendar export failed")
        raise HTTPException(status_code=502, detail=f"Google Calendar error: {str(e)}")
