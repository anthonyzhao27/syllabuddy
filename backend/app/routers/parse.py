import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.schemas import ParseResponse
from app.services.extraction import _is_image, extract_text, extract_text_from_images
from app.services.llm import extract_events

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=ParseResponse)
async def parse_syllabus(
    files: list[UploadFile] = File(default=[]),
) -> ParseResponse:
    """Extract assignments and due dates from uploaded files."""
    if not files or not files[0].filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    if _is_image(files[0]):
        text = await extract_text_from_images(files)
    else:
        if len(files) > 1:
            raise HTTPException(
                status_code=400,
                detail="Only one document file allowed. For multiple images, use screenshots.",
            )
        text = await extract_text(files[0])

    try:
        events = await extract_events(text)
    except ValueError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to parse LLM response: {e}",
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("LLM request failed during syllabus parsing")
        raise HTTPException(
            status_code=502,
            detail="LLM service unavailable. Please try again.",
        )

    return ParseResponse(events=events)
