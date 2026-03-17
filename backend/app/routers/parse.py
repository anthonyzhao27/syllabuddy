from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.models.schemas import ParseResponse
from app.services.extraction import _is_image, extract_text, extract_text_from_images
from app.services.google_docs import fetch_google_doc
from app.services.llm import extract_events

router = APIRouter()


@router.post("/", response_model=ParseResponse)
async def parse_syllabus(
    files: list[UploadFile] = File(default=[]),
    google_doc_url: Optional[str] = Form(None),
) -> ParseResponse:
    """Extract assignments and due dates from uploaded files or a Google Doc URL."""
    has_files = bool(files and files[0].filename)

    if has_files and _is_image(files[0]):
        text = await extract_text_from_images(files)
    elif has_files:
        if len(files) > 1:
            raise HTTPException(
                status_code=400,
                detail="Only one document file allowed. For multiple images, use screenshots.",
            )
        text = await extract_text(files[0])
    elif google_doc_url:
        text = await fetch_google_doc(google_doc_url)
    else:
        raise HTTPException(
            status_code=400, detail="Provide file(s) or a google_doc_url."
        )

    events = await extract_events(text)
    return ParseResponse(events=events)
