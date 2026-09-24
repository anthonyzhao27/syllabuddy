import logging
from collections import Counter
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from app.middleware.auth import AuthenticatedUser, get_current_user
from app.middleware.limiter import limiter
from app.models.schemas import LLMSyllabus, ParseResponse, ResolveRequest
from app.services.extraction import (
    classify_upload,
    extract_text,
    extract_text_from_images,
)
from app.services.llm import extract_syllabus, resolve_extraction
from app.services import storage as storage_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=ParseResponse)
@limiter.limit("10/hour;30/day")
async def parse_syllabus(
    request: Request,
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

    first_kind = await classify_upload(files[0])

    if first_kind == "image":
        for file in files[1:]:
            kind = await classify_upload(file)
            if kind != "image":
                raise HTTPException(
                    status_code=400,
                    detail=("When uploading screenshots, all files must be images."),
                )
        text = await extract_text_from_images(files, user.access_token)
    else:
        if len(files) > 1:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Only one document file allowed. "
                    "For multiple images, use screenshots."
                ),
            )
        text = await extract_text(files[0], user.access_token, mime=first_kind)

    try:
        outcome = await extract_syllabus(text, today=date.today())
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

    events = outcome.events
    course_codes = [event.course.strip() for event in events if event.course.strip()]
    course_code = Counter(course_codes).most_common(1)[0][0] if course_codes else None

    return ParseResponse(
        events=events,
        course_code=course_code,
        term_context=outcome.term_context,
        extraction=(
            outcome.extraction.model_dump(mode="json") if outcome.extraction else None
        ),
    )


@router.post("/resolve", response_model=ParseResponse)
@limiter.limit("120/hour")
async def resolve_syllabus_dates(
    request: Request,
    body: ResolveRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> ParseResponse:
    """Re-date a parsed syllabus with a corrected term anchor. No LLM call."""
    try:
        extraction = LLMSyllabus.model_validate(body.extraction)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid extraction payload.")

    events, ctx = resolve_extraction(
        extraction, body.today or date.today(), body.override
    )
    logger.info(
        "syllabus_resolve anchor=%s year=%s override=%s",
        ctx.anchor_source,
        ctx.year_source,
        body.override.model_dump(exclude_none=True, mode="json"),
    )
    return ParseResponse(
        events=events,
        course_code=extraction.course_code or None,
        term_context=ctx,
        extraction=extraction.model_dump(mode="json"),
    )
