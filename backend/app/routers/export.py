from fastapi import APIRouter

from app.models.schemas import ExportRequest

router = APIRouter()


@router.post("/")
async def export_calendar(request: ExportRequest):
    """Export parsed events to Google Calendar or .ics file."""
    # TODO: call calendar service
    return {"status": "not implemented"}
