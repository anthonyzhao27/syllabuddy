import logging
from collections import Counter

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.middleware.auth import AuthenticatedUser, get_current_user
from app.models.schemas import ParseResponse
from app.services.extraction import _is_image, extract_text, extract_text_from_images
from app.services.llm import extract_events
from app.services import storage as storage_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=ParseResponse)
async def parse_syllabus(
    files: list[UploadFile] = File(default=[]),
    user: AuthenticatedUser = Depends(get_current_user),
) -> ParseResponse:
    """Extract assignments and due dates from uploaded files.

    This endpoint only parses the syllabus and returns the extracted events.
    To save the syllabus and events, use POST /files/ after reviewing.
    """
    if not files or not files[0].filename:
        raise HTTPException(status_code=400, detail="Please upload a file.")

    await storage_service.validate_total_upload_size(files)

    if _is_image(files[0]):
        if not all(_is_image(file) for file in files):
            raise HTTPException(
                status_code=400,
                detail="When uploading screenshots, all files must be images.",
            )
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

    course_codes = [event.course.strip() for event in events if event.course.strip()]
    course_code = Counter(course_codes).most_common(1)[0][0] if course_codes else None

    return ParseResponse(events=events, course_code=course_code)
