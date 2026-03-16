from fastapi import APIRouter, UploadFile, File

from app.models.schemas import ParseResponse

router = APIRouter()


@router.post("/", response_model=ParseResponse)
async def parse_syllabus(file: UploadFile = File(...)):
    """Extract assignments and due dates from an uploaded syllabus."""
    # TODO: extract text via extraction service
    # TODO: send text to LLM for structured extraction
    return ParseResponse(events=[])
