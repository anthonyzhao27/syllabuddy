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
    OutlookExportResponse,
)
from app.services.google_calendar import export_to_google_calendar_sync
from app.services.ics import create_ics
from app.services.outlook import generate_outlook_deep_link

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

    ics_content = create_ics(request.events, request.timezone)

    filename = request.filename
    if not filename.endswith(".ics"):
        filename += ".ics"

    return Response(
        content=ics_content,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/outlook")
async def export_outlook(request: OutlookExportRequest):
    """Export events to Outlook. Single event returns deep link, multiple returns ICS."""
    if not request.events:
        raise HTTPException(status_code=400, detail="No events to export")

    if len(request.events) == 1:
        url = generate_outlook_deep_link(request.events[0], request.timezone)
        return OutlookExportResponse(method="deep_link", url=url)
    else:
        ics_content = create_ics(request.events, request.timezone)
        return Response(
            content=ics_content,
            media_type="text/calendar; charset=utf-8",
            headers={
                "Content-Disposition": 'attachment; filename="syllabus-outlook.ics"'
            },
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
            request.calendar_id,
            request.timezone,
        )
        return GoogleExportResponse(**result)
    except Exception as e:
        logger.exception("Google Calendar export failed")
        raise HTTPException(status_code=502, detail=f"Google Calendar error: {str(e)}")
