"""Calendar export endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response

from app.middleware.auth import AuthenticatedUser, get_current_user
from app.middleware.limiter import limiter
from app.models.schemas import (
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
from app.services.ics import create_ics

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ics")
@limiter.limit("30/hour")
async def export_ics(
    request: Request,
    body: IcsExportRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> Response:
    """Generate and return an .ics file for download."""
    if not body.events:
        raise HTTPException(status_code=400, detail="No events to export")

    try:
        course_code = validate_and_get_course_code(body.events)
        calendar_name = get_calendar_name(course_code)
    except (MissingCourseCodeError, MixedCourseError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    ics_content = create_ics(body.events, body.timezone, calendar_name)
    filename = f"{sanitize_filename(calendar_name)}.ics"

    return Response(
        content=ics_content,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/outlook")
@limiter.limit("30/hour")
async def export_outlook(
    request: Request,
    body: OutlookExportRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> Response:
    """Export events to Outlook as ICS file."""
    if not body.events:
        raise HTTPException(status_code=400, detail="No events to export")

    try:
        course_code = validate_and_get_course_code(body.events)
        calendar_name = get_calendar_name(course_code)
    except (MissingCourseCodeError, MixedCourseError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    ics_content = create_ics(body.events, body.timezone, calendar_name)
    filename = f"{sanitize_filename(calendar_name)}.ics"

    return Response(
        content=ics_content,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
